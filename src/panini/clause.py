"""RLCD clause AST and its constraint layer (docs/RLCD_TRANSITION_PLAN.md, stage 2).

A clause is one finite verb and its participants, in the shape of
data/schemas/rlcd-clause.schema.json. Vidyut derives a form for almost anything it is
given, including invented roots and impossible voice-number combinations (plan section
1.2), so check() decides first whether a clause is licit. It is pure: no Vidyut, no
PyTorch. The Dhatupatha index, the karmakatva table and the stem table are passed in,
so the same logic can be ported to Rust and run against the shared fixtures
(data/rlcd/clause_fixtures.jsonl, plan section 7).

Violation codes are stable identifiers shared with the fixtures. The sutra references
are the draft basis for each check and await the grammarian's review
(docs/RLCD_CONSTRAINTS.md).
"""

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "data/schemas/rlcd-clause.schema.json"
KARMAKATVA = ROOT / "data/rlcd/dhatu_constraints.tsv"
STEMS = ROOT / "data/rlcd/stem_lexicon.tsv"

# Person of a participant (1.4.105, 1.4.107, 1.4.108).
PURUSHA_OF_STEM = {"asmad": "Uttama", "yuzmad": "Madhyama"}

# Case of each role (2.3.2, 2.3.18, 2.3.36); the participant the verb expresses (abhihita) is in the first case (2.3.46).
VIBHAKTI = {
    ("kartf", "Kartari"): "Prathama", ("kartf", "Karmani"): "Trtiya", ("kartf", "Bhave"): "Trtiya",
    ("karman", "Kartari"): "Dvitiya", ("karman", "Karmani"): "Prathama",
    ("karaRa", None): "Trtiya", ("aDikaraRa", None): "Saptami",
}
WORD_ORDER = ("kartf", "aDikaraRa", "karaRa", "karman")
AGREES_WITH = {"Kartari": "kartf", "Karmani": "karman"}

VIOLATIONS = {
    "SCHEMA": "does not match data/schemas/rlcd-clause.schema.json",
    "DHATU_UNKNOWN": "root, gana and code are not one Dhatupatha entry",
    "KARMAKATVA_UNKNOWN": "transitivity of this root with these upasargas is not in the reviewed table",
    "KARMANI_NEEDS_SAKARMAKA": "karmani prayoga needs a transitive root (3.4.69)",
    "BHAVE_NEEDS_AKARMAKA": "bhave prayoga needs an intransitive root (3.4.69)",
    "BHAVE_FORM": "bhave prayoga takes prathama purusha, ekavacana (1.4.22, 1.4.108)",
    "BHAVE_NO_KARMAN": "bhave prayoga has no karman",
    "KARMAN_NEEDS_SAKARMAKA": "an intransitive root takes no karman (1.4.49)",
    "ROLE_COUNT": "each role appears at most once in schema v0.3",
    "AGREEMENT_MISSING": "the participant the verb agrees with is missing (ellipsis is not modelled in v0.3)",
    "AGREEMENT_PURUSHA": "verb purusha differs from the agreeing participant's (1.4.105-1.4.108)",
    "AGREEMENT_VACANA": "verb vacana differs from the agreeing participant's (1.4.21, 1.4.22)",
    "STEM_UNKNOWN": "stem is not in the reviewed stem table",
    "LINGA_MISMATCH": "the stem table does not list this gender for the stem",
    "NO_DERIVATION": "Vidyut derives no form (for example, a pada the root does not take)",
    "ROUND_TRIP_MISMATCH": "the derived form is in the lexicon only with other analyses",
    "ENGINE_DEFECT": "Vidyut 0.4.0 derives a wrong form for this combination; blocked until fixed upstream",
}


@dataclass(frozen=True)
class Violation:
    code: str
    detail: str = ""

    def to_json(self):
        return {"code": self.code, "detail": self.detail}


def schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def structural_errors(clause, spec=None):
    """Shape and enum errors against the JSON Schema, as plain strings (no jsonschema dependency)."""
    spec = spec or schema()
    defs, props, errors = spec["$defs"], spec["properties"], []

    def enum(ref_or_spec):
        node = defs[ref_or_spec["$ref"].split("/")[-1]] if "$ref" in ref_or_spec else ref_or_spec
        return node.get("enum")

    if not isinstance(clause, dict):
        return ["clause is not an object"]
    for key in spec["required"]:
        if key not in clause:
            errors.append(f"missing {key}")
    for key in clause:
        if key not in props:
            errors.append(f"unknown field {key}")
    if errors:
        return errors
    if clause["schema_version"] != props["schema_version"]["const"]:
        errors.append("schema_version must be " + props["schema_version"]["const"])
    for key in ("prayoga", "lakara", "purusha", "vacana", "dhatu_pada"):
        if key in clause and clause[key] not in enum(props[key]):
            errors.append(f"{key} {clause[key]!r} not allowed")
    dhatu, dspec = clause["dhatu"], props["dhatu"]
    if not isinstance(dhatu, dict) or set(dhatu) != set(dspec["required"]):
        errors.append("dhatu needs exactly " + ", ".join(dspec["required"]))
    elif dhatu["gana"] not in dspec["properties"]["gana"]["enum"]:
        errors.append(f"gana {dhatu['gana']!r} not allowed")
    upasargas = clause["upasargas"]
    if not isinstance(upasargas, list) or len(upasargas) > props["upasargas"]["maxItems"]:
        errors.append("upasargas must be a list of at most 3")
    else:
        errors += [f"upasarga {u!r} not allowed" for u in upasargas if u not in defs["upasarga"]["enum"]]
    participants = clause["participants"]
    pspec = defs["participant"]
    if not isinstance(participants, list) or len(participants) > props["participants"]["maxItems"]:
        errors.append("participants must be a list of at most 4")
        return errors
    for i, p in enumerate(participants):
        if not isinstance(p, dict) or set(p) != set(pspec["required"]):
            errors.append(f"participant {i} needs exactly " + ", ".join(pspec["required"]))
            continue
        for key in ("role", "linga", "vacana"):
            if p[key] not in enum(pspec["properties"][key]):
                errors.append(f"participant {i} {key} {p[key]!r} not allowed")
    return errors


def read_tsv(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:] if line]


def load_karmakatva(path=KARMAKATVA):
    """(code, upasargas tuple) -> 'sakarmaka' | 'akarmaka'; rows list unprefixed roots in v0.3."""
    return {(row["code"], ()): row["karmakatva"] for row in read_tsv(path)}


def load_stems(path=STEMS):
    """stem -> {"lingas": set of gender names, "kind": "basic" | "nyap"}.

    Gender comes from this reviewed table, not from the Vidyut kosha: the kosha inflects
    stems in every gender (it lists aSvA as a feminine form of aSva), so it cannot say which
    genders a stem takes. nyap stems end in a feminine suffix (nadI, sItA) and decline
    correctly only when Vidyut is told so.
    """
    return {row["stem"]: {"lingas": set(row["lingas"].split(",")), "kind": row["kind"]} for row in read_tsv(path)}


def vibhakti(role, prayoga):
    return VIBHAKTI.get((role, prayoga)) or VIBHAKTI[(role, None)]


def participant_purusha(stem):
    return PURUSHA_OF_STEM.get(stem, "Prathama")


def check(clause, dhatupatha, karmakatva, stems):
    """Violations of a clause, empty if it is licit under schema v0.3.

    dhatupatha: set of (code, aupadeshika, gana). karmakatva: load_karmakatva() table.
    stems: load_stems() table.
    """
    errors = structural_errors(clause)
    if errors:
        return [Violation("SCHEMA", "; ".join(errors))]
    out = []
    d = clause["dhatu"]
    if (d["code"], d["aupadeshika"], d["gana"]) not in dhatupatha:
        out.append(Violation("DHATU_UNKNOWN", f"{d['code']} {d['aupadeshika']} {d['gana']}"))
    prayoga, roles = clause["prayoga"], [p["role"] for p in clause["participants"]]
    for role in sorted({r for r in roles if roles.count(r) > 1}):
        out.append(Violation("ROLE_COUNT", role))
    kind = karmakatva.get((d["code"], tuple(clause["upasargas"])))
    if kind is None:
        out.append(Violation("KARMAKATVA_UNKNOWN", f"{d['code']} with upasargas {clause['upasargas']}"))
    else:
        if prayoga == "Karmani" and kind != "sakarmaka":
            out.append(Violation("KARMANI_NEEDS_SAKARMAKA", d["aupadeshika"]))
        if prayoga == "Bhave" and kind != "akarmaka":
            out.append(Violation("BHAVE_NEEDS_AKARMAKA", d["aupadeshika"]))
        if "karman" in roles and kind != "sakarmaka":
            out.append(Violation("KARMAN_NEEDS_SAKARMAKA", d["aupadeshika"]))
    if prayoga == "Bhave":
        if (clause["purusha"], clause["vacana"]) != ("Prathama", "Eka"):
            out.append(Violation("BHAVE_FORM", f"{clause['purusha']} {clause['vacana']}"))
        if "karman" in roles:
            out.append(Violation("BHAVE_NO_KARMAN"))
    else:
        role = AGREES_WITH[prayoga]
        agreeing = [p for p in clause["participants"] if p["role"] == role]
        if not agreeing:
            out.append(Violation("AGREEMENT_MISSING", role))
        else:
            p = agreeing[0]
            if participant_purusha(p["stem"]) != clause["purusha"]:
                out.append(Violation("AGREEMENT_PURUSHA", f"{p['stem']} needs {participant_purusha(p['stem'])}"))
            if p["vacana"] != clause["vacana"]:
                out.append(Violation("AGREEMENT_VACANA", f"{p['stem']} is {p['vacana']}"))
    for p in clause["participants"]:
        entry = stems.get(p["stem"])
        if entry is None:
            out.append(Violation("STEM_UNKNOWN", p["stem"]))
        elif p["linga"] not in entry["lingas"]:
            out.append(Violation("LINGA_MISMATCH", f"{p['stem']} is {', '.join(sorted(entry['lingas']))}"))
    return out


def ordered_participants(clause):
    return sorted(clause["participants"], key=lambda p: WORD_ORDER.index(p["role"]))
