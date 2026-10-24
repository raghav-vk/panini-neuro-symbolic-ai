"""CPU baselines, tiny byte Transformer, and denominator-explicit evaluation."""

import math
import random
from collections import Counter


def model_text(record, candidate, use_rules=True, use_context=True, mark_boundary=False):
    # Never expose gold indices, lemmas, review metadata or the gold rule_id.
    fields = [record["surface"], candidate["left"], candidate["right"]]
    if mark_boundary:
        # The candidates of one surface differ only here, so spell the junction out.
        fields.append(candidate["left"][-2:] + "|" + candidate["right"][:2])
    if use_rules:
        fields.append(",".join(sorted({p["rule_id"] for p in candidate["proofs"]})))
    if use_context:
        context = record.get("context", "")
        if context:
            fields.append(context)
    return "\x1f".join(fields)


LONG_VOWELS = ("ai", "au", "ā", "ī", "ū", "ṝ", "ḹ", "e", "o")


def boundary_long_vowels(candidate):
    """Long vowels at the restored boundary: left word's final, right word's initial."""
    left, right = candidate["left"], candidate["right"]
    return any(left.endswith(v) for v in LONG_VOWELS) + any(right.startswith(v) for v in LONG_VOWELS)


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
            elif self.name == "frequency_short_vowel":
                # Frequency, with ties broken toward short boundary vowels: the explicit form of
                # the preference that alphabetical index tie-breaking hides.
                value = sum(math.log1p(self.words[w]) for w in (c["left"], c["right"]))
                value += math.log1p(max((self.rules[p["rule_id"]] for p in c["proofs"]), default=0))
                value -= 1e-3 * boundary_long_vowels(c)
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
    groups, reciprocal, predictions, tie_averaged, tied = {}, 0.0, [], 0.0, 0
    for row, values in zip(rows, scores, strict=True):
        if len(values) != len(row["candidates"]) or any(not math.isfinite(x) for x in values):
            raise ValueError("invalid candidate scores")
        order = sorted(range(len(values)), key=lambda i: (-values[i], i))
        gold = row["gold_indices"]
        hit = bool(order and order[0] in gold)
        # Index order is alphabetical, so breaking ties by index is a hidden heuristic.
        best = [i for i in order if values[i] == values[order[0]]] if order else []
        tied += len(best) > 1
        tie_averaged += sum(i in gold for i in best) / len(best) if best else 0
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
            "top1_tie_averaged": rate(tie_averaged, total), "tied_top_rows": tied,
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


def build_lexicon(train, external=False, boundary_vowels=False):
    """Training-split word and rule counts for the optional lexical feature head.

    external adds the candidates' kosha_left/kosha_right flags (scripts/annotate_lexicon.py) as features;
    boundary_vowels adds the long-vowel count at the restored boundary.
    """
    left, right, rules = Counter(), Counter(), Counter()
    for row in train:
        left[row["left"]] += 1
        right[row["right"]] += 1
        rules[row["rule_id"]] += 1
    return {"left": dict(left), "right": dict(right), "rules": dict(rules), "external": external,
            "boundary_vowels": boundary_vowels}


LEXICAL_FEATURES = 5


def lexical_features(lexicon, row, candidate, exclude_self=False, use_rules=True):
    """Counts for one candidate; exclude_self drops a training row's own occurrence (leave-one-out).

    Without use_rules the rule-frequency feature is zero, so the no-rules ablation sees no rule identity.
    """
    left = lexicon["left"].get(candidate["left"], 0)
    right = lexicon["right"].get(candidate["right"], 0)
    rule = max((lexicon["rules"].get(p["rule_id"], 0) for p in candidate["proofs"]), default=0) if use_rules else 0
    if exclude_self:
        # Otherwise "seen in training" would mark every training gold and nothing at evaluation time.
        left -= candidate["left"] == row["left"]
        right -= candidate["right"] == row["right"]
    features = [math.log1p(left), math.log1p(right), float(left > 0), float(right > 0), math.log1p(rule)]
    if lexicon.get("external"):
        features += [float(candidate["kosha_left"]), float(candidate["kosha_right"])]
    if lexicon.get("boundary_vowels"):
        features.append(float(boundary_long_vowels(candidate)))
    return features


def feature_count(lexicon):
    return LEXICAL_FEATURES + 2 * bool(lexicon.get("external")) + bool(lexicon.get("boundary_vowels"))


class LinearBaseline:
    """Linear ranker over the lexical-head features alone, ties broken toward short boundary vowels.

    The strongest non-neural comparison for the feature head: same inputs, no Transformer.
    """

    def __init__(self, train, external=False, epochs=20, seed=7):
        import torch
        torch.manual_seed(seed)
        self.lexicon = build_lexicon(train, external)
        self.linear = torch.nn.Linear(feature_count(self.lexicon), 1)
        optimizer = torch.optim.AdamW(self.linear.parameters(), lr=0.01)
        rows = [r for r in train if r["gold_indices"]]
        features = [torch.tensor([lexical_features(self.lexicon, r, c, exclude_self=True) for c in r["candidates"]]) for r in rows]
        for epoch in range(epochs):
            order = list(range(len(rows)))
            random.Random(seed + epoch).shuffle(order)
            for start in range(0, len(order), 64):
                batch = order[start:start+64]
                scores = [self.linear(features[i]).squeeze(-1) for i in batch]
                loss = torch.stack([torch.logsumexp(s, 0) - torch.logsumexp(s[rows[i]["gold_indices"]], 0)
                                    for i, s in zip(batch, scores)]).mean()
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

    def score(self, row):
        import torch
        if not row["candidates"]:
            return []
        with torch.no_grad():
            values = self.linear(torch.tensor([lexical_features(self.lexicon, row, c) for c in row["candidates"]])).squeeze(-1).tolist()
        return [v - 1e-3 * boundary_long_vowels(c) for v, c in zip(values, row["candidates"])]


def make_transformer(width=64, layers=2, heads=4, max_length=192, pooling="mean", mark_boundary=False, lexicon=None):
    import torch
    from torch import nn

    class TinyRanker(nn.Module):
        def __init__(self):
            super().__init__()
            if pooling not in {"mean", "cls"}:
                raise ValueError("pooling must be mean or cls")
            self.max_length, self.pooling, self.mark_boundary = max_length, pooling, mark_boundary
            # Byte b is token b + 1; 0 pads; 257 is the summary token for cls pooling.
            self.embedding = nn.Embedding(258 if pooling == "cls" else 257, width, padding_idx=0)
            self.position = nn.Embedding(max_length + (pooling == "cls"), width)
            layer = nn.TransformerEncoderLayer(width, heads, width * 4, dropout=0.1, batch_first=True)
            self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
            self.output = nn.Linear(width, 1)
            self.lexicon = lexicon
            if lexicon is not None:
                self.lexical = nn.Linear(feature_count(lexicon), 1)

        def forward(self, tokens, features=None):
            if self.pooling == "cls":
                tokens = torch.cat([torch.full((tokens.shape[0], 1), 257, dtype=tokens.dtype), tokens], 1)
            padding = tokens == 0
            x = self.embedding(tokens) + self.position(torch.arange(tokens.shape[1]))
            x = self.encoder(x, src_key_padding_mask=padding)
            if self.pooling == "cls":
                x = x[:, 0]
            else:
                x = (x * (~padding).unsqueeze(-1)).sum(1) / (~padding).sum(1, keepdim=True)
            score = self.output(x).squeeze(-1)
            if self.lexicon is not None:
                score = score + self.lexical(features).squeeze(-1)
            return score

    return TinyRanker()


def score_neural(model, rows, use_rules=True, use_context=True, gradients=False, exclude_self=False):
    import torch
    texts = [model_text(r, c, use_rules, use_context, model.mark_boundary).encode("utf-8") for r in rows for c in r["candidates"]]
    if not texts:
        return [torch.empty(0) for _ in rows]
    if max(map(len, texts)) > model.max_length:
        raise ValueError("candidate input exceeds max_length; increase it, do not silently truncate")
    tokens = torch.zeros((len(texts), max(map(len, texts))), dtype=torch.long)
    for i, text in enumerate(texts):
        tokens[i, :len(text)] = torch.tensor([x + 1 for x in text])
    features = None
    if model.lexicon is not None:
        features = torch.tensor([lexical_features(model.lexicon, r, c, exclude_self, use_rules) for r in rows for c in r["candidates"]])
    with torch.set_grad_enabled(gradients):
        scores = model(tokens, features)
    return list(scores.split([len(r["candidates"]) for r in rows]))


def predict_neural(model, rows, use_rules=True, use_context=True):
    model.eval()
    return [s.tolist() for start in range(0, len(rows), 16)
            for s in score_neural(model, rows[start:start+16], use_rules, use_context)]


def train_neural(train, dev, seed=7, epochs=3, width=64, layers=2, use_rules=True, use_context=True, max_length=192,
                 pooling="mean", mark_boundary=False, lexical=False, external_lexicon=False, boundary_vowel_feature=False):
    import copy
    import torch
    torch.manual_seed(seed)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    model = make_transformer(width, layers, max_length=max_length, pooling=pooling, mark_boundary=mark_boundary,
                             lexicon=build_lexicon(train, external_lexicon, boundary_vowel_feature)
                             if lexical or external_lexicon or boundary_vowel_feature else None)
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
            scores = score_neural(model, batch, use_rules, use_context, gradients=True, exclude_self=True)
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
