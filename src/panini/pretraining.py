"""Self-supervised pretraining (protocol section 11.3, docs/PRETRAINING_PLAN.md).

Two parts: decontaminated corpora P-A and P-B built from DCS_pick (plan section 3),
and a byte-level encoder pretrained with span masking and rule-guided
real-or-near-miss discrimination (plan sections 4 and 5). The kosha is never read here.
"""

import math
import random
from collections import defaultdict

from .translit import SLP1_LETTERS, SLP1_VOWELS, iast_to_slp1

SPAN = 30
MIN_SHARED_SPANS = 2


# DCS_pick writes three SLP1 vowels as other characters; the vowel list "aAiIuUfṝ±²" (sent 14324)
# and forms such as BrAtṝn and k±pta fix the reading.
DCS_PICK_VOWELS = str.maketrans({"ṝ": "F", "±": "x", "²": "X"})


def normalize(text):
    return " ".join(text.translate(DCS_PICK_VOWELS).split())


def is_slp1_text(text):
    """Editorial markers ("[... O6 ZeiCenJ]"), digits and unknown signs fail."""
    return set(text) <= SLP1_LETTERS | {" "}


def spans(text, size=SPAN):
    return {text[i:i + size] for i in range(len(text) - size + 1)}


def sentence_lemmas(sentence):
    """DCS_pick lemmas are IAST (protocol amendment 0.6); held-out lemmas are SLP1."""
    return {iast_to_slp1(lemma) for word in sentence["lemmas"] for lemma in word}


def build_corpora(sentences, held_ids, held_lemmas, span=SPAN, min_shared=MIN_SHARED_SPANS):
    """Return P-A, P-B and the removal record.

    P-A drops the held-out source sentences, their exact copies (after whitespace
    normalisation) and near copies: sentences sharing at least min_shared distinct
    span-character substrings with any held-out sentence. P-B is P-A minus every
    sentence whose DCS lemmas include a held-out right-word lemma. Sentences with characters
    outside SLP1 after normalisation are dropped from both, after the duplicate checks.
    """
    held = [s for s in sentences if s["sent_id"] in held_ids]
    if len(held) != len(held_ids):
        raise ValueError("held-out sentence IDs missing from the corpus")
    held_text = {normalize(s["sentence"]): s["sent_id"] for s in held}
    held_spans = defaultdict(set)
    for s in held:
        for piece in spans(normalize(s["sentence"]), span):
            held_spans[piece].add(s["sent_id"])
    removed = {"held_out": sorted(held_ids), "exact_duplicate": [], "near_duplicate": [], "held_lemma": [], "not_slp1": []}
    pa, pb = [], []
    for s in sentences:
        if s["sent_id"] in held_ids:
            continue
        text = normalize(s["sentence"])
        shared = spans(text, span) & held_spans.keys()
        if text in held_text:
            removed["exact_duplicate"].append({"sent_id": s["sent_id"], "copy_of": held_text[text]})
        elif len(shared) >= min_shared:
            matches = defaultdict(int)
            for piece in shared:
                for held_id in held_spans[piece]:
                    matches[held_id] += 1
            removed["near_duplicate"].append({"sent_id": s["sent_id"], "shared_spans": len(shared),
                                              "closest": max(matches, key=lambda k: (matches[k], -k))})
        elif not is_slp1_text(text):
            removed["not_slp1"].append(s["sent_id"])
        elif text:
            row = {"sent_id": s["sent_id"], "text": text}
            pa.append(row)
            if sentence_lemmas(s) & held_lemmas:
                removed["held_lemma"].append(s["sent_id"])
            else:
                pb.append(row)
    return pa, pb, removed


# --- Rule-guided near misses (plan section 5, objective 2) ---


def vowel_confusions(rules):
    """Boundary vowels the rules cannot tell apart, derived from the rules themselves.

    Two right-word initial vowels are confusable if, after the same left vowel, they give
    the same junction string; likewise for left-word final vowels. For the 18 draft rules
    this is vowel length (a/A, i/I, u/U) at both ends, plus e/E and o/O word-initially.
    """
    junctions = defaultdict(set)
    for rule in rules:
        for left in rule.match.left_suffixes:
            for right in rule.match.right_prefixes:
                if left in SLP1_VOWELS and right in SLP1_VOWELS:
                    junctions[(left, right)].add((left if rule.operation.left == "keep_match" else "")
                                                 + rule.operation.emit
                                                 + (right if rule.operation.right == "keep_match" else ""))
    initial, final = defaultdict(set), defaultdict(set)
    for (l1, r1), out1 in junctions.items():
        for (l2, r2), out2 in junctions.items():
            if out1 & out2:
                if l1 == l2 and r1 != r2:
                    initial[r1].add(r2)
                if r1 == r2 and l1 != l2:
                    final[l1].add(l2)
    return {"initial": {k: sorted(v) for k, v in sorted(initial.items())},
            "final": {k: sorted(v) for k, v in sorted(final.items())}}


def near_misses(word, confusions, vocabulary):
    """Altered forms of word at its first or last vowel, never an attested corpus word."""
    out = set()
    if word[:1] in confusions["initial"]:
        out.update(v + word[1:] for v in confusions["initial"][word[0]])
    if word[-1:] in confusions["final"]:
        out.update(word[:-1] + v for v in confusions["final"][word[-1]])
    return sorted(out - vocabulary - {word})


def corpus_vocabulary(texts):
    return {w for t in texts for w in t.split(" ")}


# --- Encoding ---

PAD, CLS, MASK = 0, 257, 258  # byte b is token b + 1, as in ranking.make_transformer
VOCAB = 259


def encode(text):
    return [b + 1 for b in text.encode("ascii")]


def word_ids(text):
    """Word index of every byte; -1 for spaces."""
    ids, word = [], 0
    for ch in text:
        if ch == " ":
            ids.append(-1)
            word += 1
        else:
            ids.append(word)
    return ids


def mask_spans(tokens, rng, rate=0.15, mean_span=3.0):
    """Mask about rate of the bytes in spans of geometric length with the given mean."""
    n = len(tokens)
    target = max(1, round(rate * n))
    masked = set()
    while len(masked) < target:
        length = 1
        while rng.random() > 1 / mean_span:
            length += 1
        start = rng.randrange(n)
        for i in range(start, min(n, start + length)):
            if len(masked) < target:
                masked.add(i)
    inputs, labels = list(tokens), [-100] * n
    for i in masked:
        labels[i], inputs[i] = tokens[i], MASK
    return inputs, labels


def alter_words(text, confusions, vocabulary, rng, rate=0.15, cache=None):
    """Replace about rate of the alterable words with a rule-guided near miss.

    Returns the new text and one label per word: 1 altered, 0 attested, -100 if the word
    has no near miss (excluded from the loss, so the task is not "can this word change").
    """
    words, labels = text.split(" "), []
    for i, word in enumerate(words):
        if cache is None:
            options = near_misses(word, confusions, vocabulary)
        elif word in cache:
            options = cache[word]
        else:
            options = cache[word] = near_misses(word, confusions, vocabulary)
        if not options:
            labels.append(-100)
        elif rng.random() < rate:
            words[i] = rng.choice(options)
            labels.append(1)
        else:
            labels.append(0)
    return " ".join(words), labels


# --- Model ---

SIZES = {"S": {"width": 256, "layers": 6, "heads": 8}, "M": {"width": 512, "layers": 6, "heads": 8}}


def make_encoder(width=256, layers=6, heads=8, max_length=256, dropout=0.1):
    """Bidirectional byte encoder; embedding, position and encoder match ranking.make_transformer."""
    import torch
    from torch import nn

    class PretrainEncoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.max_length = max_length
            self.config = {"width": width, "layers": layers, "heads": heads, "max_length": max_length}
            self.embedding = nn.Embedding(VOCAB, width, padding_idx=PAD)
            self.position = nn.Embedding(max_length, width)
            layer = nn.TransformerEncoderLayer(width, heads, width * 4, dropout=dropout, batch_first=True)
            self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
            self.mlm = nn.Linear(width, VOCAB)
            self.discriminator = nn.Linear(width, 1)

        def forward(self, tokens):
            padding = tokens == PAD
            x = self.embedding(tokens) + self.position(torch.arange(tokens.shape[1], device=tokens.device))
            return self.encoder(x, src_key_padding_mask=padding)

        def word_logits(self, hidden, ids, words):
            """Mean discriminator logit over each word's bytes: (batch, words). Fixed shapes for MPS."""
            byte = self.discriminator(hidden).squeeze(-1)
            onehot = (ids.unsqueeze(-1) == torch.arange(words, device=ids.device)).to(byte.dtype)
            return torch.einsum("bt,btw->bw", byte, onehot) / onehot.sum(1).clamp(min=1)

    return PretrainEncoder()


def padded(n, step):
    """Round up so MPS sees a handful of shapes instead of a new graph per batch."""
    return -(-n // step) * step


def batch_mlm(texts, rng, device, max_length=256):
    import torch
    pairs = [mask_spans(encode(t), rng) for t in texts]
    length = min(max_length, padded(max(len(p[0]) for p in pairs), 64))
    tokens = torch.full((len(texts), length), PAD, dtype=torch.long)
    labels = torch.full((len(texts), length), -100, dtype=torch.long)
    for i, (inputs, target) in enumerate(pairs):
        tokens[i, :len(inputs)] = torch.tensor(inputs)
        labels[i, :len(target)] = torch.tensor(target)
    return tokens.to(device), labels.to(device)


def batch_disc(texts, confusions, vocabulary, rng, device, cache=None, max_length=256):
    import torch
    altered = [alter_words(t, confusions, vocabulary, rng, cache=cache) for t in texts]
    length = min(max_length, padded(max(len(t) for t, _ in altered), 64))
    words = padded(max(len(w) for _, w in altered), 32)
    tokens = torch.full((len(texts), length), PAD, dtype=torch.long)
    ids = torch.full((len(texts), length), -1, dtype=torch.long)
    labels = torch.full((len(texts), words), -100, dtype=torch.long)
    for i, (text, target) in enumerate(altered):
        tokens[i, :len(text)] = torch.tensor(encode(text))
        ids[i, :len(text)] = torch.tensor(word_ids(text))
        labels[i, :len(target)] = torch.tensor(target)
    return tokens.to(device), ids.to(device), labels.to(device)


def mlm_loss(model, tokens, labels):
    """Loss, and correct and total masked bytes as device tensors (no host sync while training)."""
    import torch.nn.functional as F
    logits = model.mlm(model(tokens))
    loss = F.cross_entropy(logits.flatten(0, 1), labels.flatten(), ignore_index=-100)
    keep = labels != -100
    return loss, ((logits.argmax(-1) == labels) & keep).sum(), keep.sum()


def disc_loss(model, tokens, ids, labels):
    """Loss over words that have a near miss, and per-class counts as device tensors."""
    import torch.nn.functional as F
    logits = model.word_logits(model(tokens), ids, labels.shape[1])
    keep = (labels != -100).to(logits.dtype)
    target = labels.clamp(min=0).to(logits.dtype)
    loss = (F.binary_cross_entropy_with_logits(logits, target, reduction="none") * keep).sum() / keep.sum().clamp(min=1)
    predicted = (logits > 0).to(logits.dtype)
    return loss, {"altered": (target * keep).sum(), "altered_correct": (predicted * target * keep).sum(),
                  "attested": ((1 - target) * keep).sum(), "attested_correct": ((1 - predicted) * (1 - target) * keep).sum()}


def evaluate(model, texts, confusions, vocabulary, device, seed=0, batch_size=128):
    """Masked-byte accuracy and per-class discrimination accuracy, with fixed corruption."""
    import torch
    model.eval()
    rng = random.Random(seed)
    correct = total = 0
    counts = defaultdict(int)
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            chunk = texts[start:start + batch_size]
            _, c, n = mlm_loss(model, *batch_mlm(chunk, rng, device))
            correct, total = correct + c.item(), total + n.item()
            _, d = disc_loss(model, *batch_disc(chunk, confusions, vocabulary, rng, device))
            for k, v in d.items():
                counts[k] += int(v.item())
    model.train()
    rate = lambda a, b: a / b if b else None
    altered, attested = rate(counts["altered_correct"], counts["altered"]), rate(counts["attested_correct"], counts["attested"])
    return {"masked_byte_accuracy": rate(correct, total), "masked_bytes": total,
            "disc_altered_accuracy": altered, "disc_attested_accuracy": attested,
            "disc_balanced_accuracy": (altered + attested) / 2 if altered is not None and attested is not None else None,
            "disc_altered_words": counts["altered"], "disc_attested_words": counts["attested"]}


def learning_rate(step, steps, peak, warmup):
    if step < warmup:
        return peak * (step + 1) / warmup
    return peak * 0.5 * (1 + math.cos(math.pi * min(1.0, (step - warmup) / max(1, steps - warmup))))


# --- Neural lexicon score (plan section 6.1) ---


def candidate_text(record, candidate, context=True):
    """Text with the fused surface replaced by the candidate's two words, and the left word's index.

    With context the words sit in their source sentence, as in pretraining; without it they stand alone.
    """
    if not context:
        return candidate["left"] + " " + candidate["right"], 0
    sentence, (start, end) = record["source_sentence"], record["source_span"]
    before = normalize(sentence[:start])
    return (normalize(" ".join((sentence[:start], candidate["left"], candidate["right"], sentence[end:]))),
            len(before.split(" ")) if before else 0)


def neural_lexicon_scores(model, rows, device, context=True, batch_size=256):
    """log P(attested) of each candidate's left and right word, from the discriminator head.

    Returns one [left, right] pair per candidate, in row and candidate order.
    """
    import torch
    import torch.nn.functional as F
    items = [candidate_text(r, c, context) for r in rows for c in r["candidates"]]
    if any(len(text) > model.max_length for text, _ in items):
        raise ValueError("candidate text exceeds max_length; nothing is truncated silently")
    model.eval()
    scores = []
    with torch.no_grad():
        for start in range(0, len(items), batch_size):
            chunk = items[start:start + batch_size]
            length = min(model.max_length, padded(max(len(t) for t, _ in chunk), 64))
            words = padded(max(len(t.split(" ")) for t, _ in chunk), 32)
            tokens = torch.full((len(chunk), length), PAD, dtype=torch.long)
            ids = torch.full((len(chunk), length), -1, dtype=torch.long)
            for i, (text, _) in enumerate(chunk):
                tokens[i, :len(text)] = torch.tensor(encode(text))
                ids[i, :len(text)] = torch.tensor(word_ids(text))
            logits = model.word_logits(model(tokens.to(device)), ids.to(device), words)
            index = torch.tensor([[w, w + 1] for _, w in chunk], device=logits.device)
            # The head predicts "altered"; log sigmoid of minus that logit is log P(attested).
            scores += F.logsigmoid(-logits.gather(1, index)).cpu().tolist()
    return scores


def load_encoder(path, device="cpu"):
    import torch
    state = torch.load(path, map_location="cpu", weights_only=True)
    model = make_encoder(**state["config"], dropout=0.0)
    model.load_state_dict(state["state_dict"])
    return model.to(device).eval(), state


def init_from_pretrained(ranker, state):
    """Copy a pretrained encoder into a ranking.make_transformer model (plan section 6.2).

    Encoder layers must match exactly. Embedding rows and positions are copied as far as both
    have them; ranker positions beyond the pretraining length keep their random start.
    """
    import torch
    weights = state["state_dict"]
    with torch.no_grad():
        for name, value in ranker.state_dict().items():
            if name.startswith("encoder."):
                if weights[name].shape != value.shape:
                    raise ValueError(f"{name}: pretrained {tuple(weights[name].shape)} != ranker {tuple(value.shape)}")
                value.copy_(weights[name])
            elif name in ("embedding.weight", "position.weight"):
                if weights[name].shape[1] != value.shape[1]:
                    raise ValueError("pretrained width differs from the ranker's")
                rows = min(len(value), len(weights[name]))
                value[:rows] = weights[name][:rows]
    return ranker
