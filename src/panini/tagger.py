"""RLCD stage 3 tagger: five Choice heads over the byte encoder (docs/RLCD_TRANSITION_PLAN.md,
"Stage 3 Training Pre-Registered Settings").

Input is a sentence's pada-patha (SLP1 word forms joined by spaces). Each word's vector is
the mean of its bytes' final hidden states; each head is one linear layer over it. Every head
has a NONE option for "not applicable". Labels come from panini.dcs_conllu.
"""

from panini.pretraining import PAD, SIZES, encode, make_encoder, padded, word_ids
from panini.translit import SLP1_LETTERS

MAX_BYTES = 256
HEADS = {
    "vibhakti": ["Prathama", "Dvitiya", "Trtiya", "Caturthi", "Panchami", "Sasthi", "Saptami", "Sambodhana",
                 "compound_member", "NONE"],
    "vacana": ["Eka", "Dvi", "Bahu", "NONE"],
    "linga": ["Pum", "Stri", "Napumsaka", "NONE"],
    "purusha": ["Prathama", "Madhyama", "Uttama", "NONE"],
    "lakara": ["Lat", "Lan", "VidhiLin", "Lot", "AshirLin", "Lrn", "Lit|Lun", "Lrt|Lut", "other", "NONE"],
}
INDEX = {head: {v: i for i, v in enumerate(values)} for head, values in HEADS.items()}


def tag(word):
    """Gold tag of a converted DCS word: one value per head, NONE where DCS records nothing."""
    out = []
    for head in HEADS:
        value = word.get(head, "NONE")
        if head == "lakara" and value.startswith("other"):
            value = "other"
        if head == "vibhakti" and value.startswith("other"):
            value = "NONE"
        out.append(value)
    return tuple(out)


def clean_form(form):
    """The form without characters outside SLP1; empty for DCS's "_" (no surface form given)."""
    return "".join(ch for ch in form if ch in SLP1_LETTERS)


def sentence_items(words):
    """(word index, cleaned form) for every word with a form left; the others are dropped and counted."""
    kept = [(i, clean_form(w["form"])) for i, w in enumerate(words)]
    return [(i, f) for i, f in kept if f], sum(not f for _, f in kept)


def chunks(forms, limit=MAX_BYTES):
    """Consecutive runs of whole words of at most limit bytes; an overlong word is truncated alone.

    Returns (chunks, truncated words); each chunk is a list of (word index, form) pairs.
    """
    out, current, size, truncated = [], [], 0, 0
    for i, form in enumerate(forms):
        if len(form) > limit:
            truncated += 1
            form = form[:limit]
        extra = len(form) + (1 if current else 0)
        if current and size + extra > limit:
            out.append(current)
            current, size, extra = [], 0, len(form)
        current.append((i, form))
        size += extra
    if current:
        out.append(current)
    return out, truncated


def make_tagger(state=None, size="S", dropout=0.1):
    """Encoder plus heads; state is a scripts/pretrain.py checkpoint, or None for random initialisation."""
    import torch
    from torch import nn

    config = state["config"] if state else {**SIZES[size], "max_length": MAX_BYTES}
    encoder = make_encoder(**config, dropout=dropout)
    if state:
        encoder.load_state_dict(state["state_dict"])

    class Tagger(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.heads = nn.ModuleDict({h: nn.Linear(config["width"], len(v)) for h, v in HEADS.items()})

        def forward(self, tokens, ids, words):
            """Logits per head: (batch, words, options). Fixed shapes for MPS."""
            hidden = self.encoder(tokens)
            onehot = (ids.unsqueeze(-1) == torch.arange(words, device=ids.device)).to(hidden.dtype)
            vectors = torch.einsum("btd,btw->bwd", hidden, onehot) / onehot.sum(1).clamp(min=1).unsqueeze(-1)
            return {h: layer(vectors) for h, layer in self.heads.items()}

    return Tagger()


def batch(items, device, labelled=True):
    """items: [(forms, tags or None)] for one chunk each -> tokens, ids, labels {head: (batch, words)}."""
    import torch
    texts = [" ".join(forms) for forms, _ in items]
    length = min(MAX_BYTES, padded(max(len(t) for t in texts), 64))
    words = padded(max(len(forms) for forms, _ in items), 32)
    tokens = torch.full((len(items), length), PAD, dtype=torch.long)
    ids = torch.full((len(items), length), -1, dtype=torch.long)
    labels = {h: torch.full((len(items), words), -100, dtype=torch.long) for h in HEADS}
    for i, ((forms, tags), text) in enumerate(zip(items, texts)):
        tokens[i, :len(text)] = torch.tensor(encode(text))
        ids[i, :len(text)] = torch.tensor(word_ids(text))
        if labelled:
            for j, t in enumerate(tags):
                for h, value in zip(HEADS, t):
                    labels[h][i, j] = INDEX[h][value]
    return tokens.to(device), ids.to(device), {h: v.to(device) for h, v in labels.items()}, words


def loss(logits, labels, kind="ce"):
    """Sum over heads of the mean cross-entropy or mean multi-class Brier score over labelled words."""
    import torch
    import torch.nn.functional as F
    total = 0
    for h, out in logits.items():
        y = labels[h]
        keep = y != -100
        if kind == "ce":
            total = total + F.cross_entropy(out[keep], y[keep])
        else:
            p = out[keep].softmax(-1)
            onehot = F.one_hot(y[keep], p.shape[-1]).to(p.dtype)
            total = total + ((p - onehot) ** 2).sum(-1).mean()
    return total
