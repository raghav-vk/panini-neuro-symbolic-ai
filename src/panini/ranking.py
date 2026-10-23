"""CPU baselines, tiny byte Transformer, and denominator-explicit evaluation."""

import math
import random
from collections import Counter


def model_text(record, candidate, use_rules=True, use_context=True):
    # Never expose gold indices, lemmas, review metadata or the gold rule_id.
    fields = [record["surface"], candidate["left"], candidate["right"]]
    if use_rules:
        fields.append(",".join(sorted({p["rule_id"] for p in candidate["proofs"]})))
    if use_context:
        context = record.get("context", "")
        if context:
            fields.append(context)
    return "\x1f".join(fields)


class Baseline:
    def __init__(self, name, train):
        self.name = name
        self.words, self.rules, self.grams, self.prefixes = Counter(), Counter(), Counter(), Counter()
        for row in train:
            for word in (row["left"], row["right"]):
                self.words[word] += 1
                padded = "^" + word + "$"
                self.grams.update(zip(padded, padded[1:]))
                self.prefixes.update(padded[:-1])
            self.rules[row["rule_id"]] += 1
        self.vocab_size = len(self.prefixes) + 1

    def score(self, row):
        scores = []
        for c in row["candidates"]:
            if self.name == "symbolic_order":
                value = 0.0
            elif self.name == "frequency":
                value = sum(math.log1p(self.words[w]) for w in (c["left"], c["right"]))
                value += math.log1p(max((self.rules[p["rule_id"]] for p in c["proofs"]), default=0))
            elif self.name == "character_bigram":
                value = 0.0
                for word in (c["left"], c["right"]):
                    text = "^" + word + "$"
                    value += sum(math.log((self.grams[(a, b)] + 1) / (self.prefixes[a] + self.vocab_size)) for a, b in zip(text, text[1:]))
            else:
                raise ValueError("unknown baseline")
            scores.append(value)
        return scores


def metrics(rows, scores, threshold=0.0):
    total, covered, correct, top3, proof_valid, accepted, accepted_correct = len(rows), 0, 0, 0, 0, 0, 0
    groups, reciprocal, predictions = {}, 0.0, []
    for row, values in zip(rows, scores, strict=True):
        if len(values) != len(row["candidates"]) or any(not math.isfinite(x) for x in values):
            raise ValueError("invalid candidate scores")
        order = sorted(range(len(values)), key=lambda i: (-values[i], i))
        gold = row["gold_indices"]
        hit = bool(order and order[0] in gold)
        covered += bool(gold)
        correct += hit
        top3 += any(i in gold for i in order[:3])
        rank = next((i + 1 for i, c in enumerate(order) if c in gold), None)
        reciprocal += 1 / rank if rank else 0
        confidence = 1 / sum(math.exp(v - max(values)) for v in values) if values else 0
        choose = bool(order) and confidence >= threshold
        accepted += choose
        accepted_correct += hit and choose
        if choose:
            proof_valid += any(p["output"] == row["surface"] for p in row["candidates"][order[0]]["proofs"])
        for group in (row["rule_id"], row.get("family", "unknown")):
            item = groups.setdefault(group, {"count": 0, "correct": 0, "covered": 0})
            item["count"] += 1
            item["correct"] += hit
            item["covered"] += bool(gold)
        predictions.append({"example_id": row["example_id"], "candidate_index": order[0] if choose else None,
                            "confidence": confidence, "correct": hit and choose, "gold_covered": bool(gold),
                            "scores": values, "ranked_indices": order})
    rate = lambda n, d: n / d if d else None
    # Wilson interval describes individual test items, not source-cluster uncertainty.
    if total:
        p, z = correct / total, 1.96
        center = (p + z*z/(2*total)) / (1 + z*z/total)
        half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / (1+z*z/total)
        interval = [center-half, center+half]
    else:
        interval = None
    rule_groups = [value for key, value in groups.items() if key in {r["rule_id"] for r in rows}]
    return {"examples": total, "candidate_recall": rate(covered, total), "top1": rate(correct, total),
            "macro_rule_top1": sum(g["correct"]/g["count"] for g in rule_groups)/len(rule_groups) if rule_groups else None,
            "top3": rate(top3, total), "mrr": rate(reciprocal, total), "conditional_top1": rate(correct, covered),
            "abstention_rate": rate(total-accepted, total), "accepted_accuracy": rate(accepted_correct, accepted),
            "selected_proof_consistency": rate(proof_valid, accepted), "threshold": threshold,
            "top1_wilson95_itemwise": interval, "groups": groups}, predictions


def select_threshold(dev, scores, target=0.9):
    eligible = []
    for threshold in [0.0, 0.5, 0.75, 0.9, 0.99]:
        result, _ = metrics(dev, scores, threshold)
        if result["accepted_accuracy"] is not None and result["accepted_accuracy"] >= target:
            eligible.append((1 - result["abstention_rate"], threshold))
    return max(eligible)[1] if eligible else 1.01


def make_transformer(width=64, layers=2, heads=4, max_length=192):
    import torch
    from torch import nn

    class TinyRanker(nn.Module):
        def __init__(self):
            super().__init__()
            self.max_length = max_length
            self.embedding = nn.Embedding(257, width, padding_idx=0)
            self.position = nn.Embedding(max_length, width)
            layer = nn.TransformerEncoderLayer(width, heads, width * 4, dropout=0.1, batch_first=True)
            self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
            self.output = nn.Linear(width, 1)

        def forward(self, tokens):
            padding = tokens == 0
            x = self.embedding(tokens) + self.position(torch.arange(tokens.shape[1]))
            x = self.encoder(x, src_key_padding_mask=padding)
            x = (x * (~padding).unsqueeze(-1)).sum(1) / (~padding).sum(1, keepdim=True)
            return self.output(x).squeeze(-1)

    return TinyRanker()


def score_neural(model, rows, use_rules=True, use_context=True, gradients=False):
    import torch
    texts = [model_text(r, c, use_rules, use_context).encode("utf-8") for r in rows for c in r["candidates"]]
    if not texts:
        return [torch.empty(0) for _ in rows]
    if max(map(len, texts)) > model.max_length:
        raise ValueError("candidate input exceeds max_length; increase it, do not silently truncate")
    tokens = torch.zeros((len(texts), max(map(len, texts))), dtype=torch.long)
    for i, text in enumerate(texts):
        tokens[i, :len(text)] = torch.tensor([x + 1 for x in text])
    with torch.set_grad_enabled(gradients):
        scores = model(tokens)
    return list(scores.split([len(r["candidates"]) for r in rows]))


def predict_neural(model, rows, use_rules=True, use_context=True):
    model.eval()
    return [s.tolist() for start in range(0, len(rows), 16)
            for s in score_neural(model, rows[start:start+16], use_rules, use_context)]


def train_neural(train, dev, seed=7, epochs=3, width=64, layers=2, use_rules=True, use_context=True, max_length=192):
    import copy
    import torch
    torch.manual_seed(seed)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    model = make_transformer(width, layers, max_length=max_length)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    eligible = [r for r in train if r["gold_indices"]]
    if not eligible or not dev:
        raise ValueError("need covered training examples and a nonempty development split")
    rng, best, best_state, history = random.Random(seed), -1, None, []
    for epoch in range(epochs):
        model.train()
        rng.shuffle(eligible)
        losses = []
        for start in range(0, len(eligible), 16):
            batch = eligible[start:start+16]
            scores = score_neural(model, batch, use_rules, use_context, gradients=True)
            loss = torch.stack([torch.logsumexp(s, 0) - torch.logsumexp(s[r["gold_indices"]], 0) for r, s in zip(batch, scores)]).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(loss.item())
        dev_scores = predict_neural(model, dev, use_rules, use_context)
        result, _ = metrics(dev, dev_scores)
        history.append({"epoch": epoch + 1, "loss": sum(losses)/len(losses), "dev_top1": result["top1"]})
        if result["top1"] > best:
            best, best_state = result["top1"], copy.deepcopy(model.state_dict())
    model.load_state_dict(best_state)
    return model, {"history": history, "best_dev_top1": best, "parameters": sum(p.numel() for p in model.parameters()),
                   "uncovered_training_examples_excluded_from_loss": len(train)-len(eligible)}
