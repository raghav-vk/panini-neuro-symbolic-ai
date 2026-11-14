"""Compile an RLCD clause with Vidyut, after the constraint layer (docs/RLCD_TRANSITION_PLAN.md, stage 2).

compile_clause runs panini.clause.check first and derives nothing for an illicit clause.
For a licit one it derives every word with vidyut.prakriya, keeps each form's sutra steps
as its proof, and looks each form up in the Vidyut kosha (round trip). Words are pausal
(pada-patha): external sandhi between words is not applied in schema v0.3.

Gender and stem kind come from the reviewed stem table (panini.clause.load_stems), so the
constraint layer does not depend on the kosha. The kosha includes CC BY-NC-SA material
(THIRD_PARTY_NOTICES.md); here it serves only the round-trip check, and can be switched off
(kosha=False).
"""

from pathlib import Path

from panini.clause import (PURUSHA_OF_STEM, Violation, check, load_karmakatva, load_stems, ordered_participants,
                           vibhakti)
from panini.lexicon import pausal_variants

ROOT = Path(__file__).resolve().parents[2]
VIDYUT = ROOT / "data/external/vidyut-0.4.0"

# Combinations Vidyut 0.4.0 derives wrongly, found in stage 3 by the kosha round trip.
# Bhave luN omits ciR (3.1.66 ciR BAvakarmaRoH): BU gives aBAvizwa for aBAvi, zWA asTita for asTAyi.
# Karmani luN applies it correctly (gam: agAmi).
ENGINE_DEFECTS = [
    (lambda c: c["prayoga"] == "Bhave" and c["lakara"] == "Lun", "bhave luN without ciR (3.1.66)"),
]


class Compiler:
    def __init__(self, data=VIDYUT, kosha=True):
        import vidyut.prakriya as vp
        self.vp = vp
        self.vyakarana = vp.Vyakarana()
        entries = vp.Data(str(Path(data) / "prakriya")).load_dhatu_entries()
        self.dhatupatha = {(e.code, e.dhatu.aupadeshika, e.dhatu.gana.name) for e in entries}
        self.karmakatva = load_karmakatva()
        self.stems = load_stems()
        self.kosha = None
        if kosha:
            from vidyut.kosha import Kosha
            self.kosha = Kosha(str(Path(data) / "kosha"))

    def lookup(self, form):
        entries = []
        for variant in sorted(pausal_variants(form)):
            entries += self.kosha.get(variant)
        return entries

    def subanta(self, p, case):
        vp = self.vp
        make = vp.Pratipadika.nyap if self.stems[p["stem"]]["kind"] == "nyap" else vp.Pratipadika.basic
        return self.vyakarana.derive(vp.Pada.Subanta(
            pratipadika=make(p["stem"]), linga=getattr(vp.Linga, p["linga"]),
            vibhakti=getattr(vp.Vibhakti, case), vacana=getattr(vp.Vacana, p["vacana"])))

    def tinanta(self, clause):
        vp, d = self.vp, clause["dhatu"]
        dhatu = vp.Dhatu.mula(aupadeshika=d["aupadeshika"], gana=getattr(vp.Gana, d["gana"]))
        if clause["upasargas"]:
            dhatu = dhatu.with_prefixes(clause["upasargas"])
        pada = getattr(vp.DhatuPada, clause["dhatu_pada"]) if "dhatu_pada" in clause else None
        return self.vyakarana.derive(vp.Pada.Tinanta(
            dhatu=dhatu, prayoga=getattr(vp.Prayoga, clause["prayoga"]), lakara=getattr(vp.Lakara, clause["lakara"]),
            purusha=getattr(vp.Purusha, clause["purusha"]), vacana=getattr(vp.Vacana, clause["vacana"]),
            dhatu_pada=pada))

    def round_trip(self, form, want):
        """'verified' if the kosha has form with the wanted analysis, 'not_in_lexicon' if it lacks the form,
        'mismatch' if it has the form only with other analyses."""
        entries = self.lookup(form)
        if not entries:
            return "not_in_lexicon"
        return "verified" if any(want(e) for e in entries) else "mismatch"

    def compile_clause(self, clause):
        violations = check(clause, self.dhatupatha, self.karmakatva, self.stems)
        if not violations:
            violations = [Violation("ENGINE_DEFECT", why) for test, why in ENGINE_DEFECTS if test(clause)]
        if violations:
            return {"valid": False, "violations": [v.to_json() for v in violations]}
        words, prayoga = [], clause["prayoga"]
        for p in ordered_participants(clause):
            case = vibhakti(p["role"], prayoga)
            derived = self.subanta(p, case)
            want = lambda e, p=p, case=case: (getattr(e, "pratipadika_entry", None) is not None
                                              and e.pratipadika_entry.lemma == p["stem"]
                                              and (e.linga.name == p["linga"] or p["stem"] in PURUSHA_OF_STEM)
                                              and e.vibhakti.name == case and e.vacana.name == p["vacana"])
            words.append({"role": p["role"], "stem": p["stem"], "vibhakti": case, "derived": derived, "want": want})
        d = clause["dhatu"]
        want_verb = lambda e: (getattr(e, "dhatu_entry", None) is not None
                               and e.dhatu_entry.dhatu.aupadeshika == d["aupadeshika"]
                               and e.dhatu_entry.dhatu.gana.name == d["gana"]
                               and list(e.dhatu_entry.dhatu.prefixes) == clause["upasargas"]
                               # The kosha lists bhave forms under karmani; the forms are identical (3.4.69, 3.1.67).
                               and e.prayoga.name in ({prayoga, "Karmani"} if prayoga == "Bhave" else {prayoga})
                               and e.lakara.name == clause["lakara"]
                               and e.purusha.name == clause["purusha"] and e.vacana.name == clause["vacana"])
        words.append({"role": "kriyA", "dhatu": d["aupadeshika"], "derived": self.tinanta(clause), "want": want_verb})
        out, violations = [], []
        for w in words:
            derived = w.pop("derived")  # Vidyut's order; the first form is the one shown in "text"
            want = w.pop("want")
            if not derived:
                violations.append(Violation("NO_DERIVATION", w.get("stem") or w["dhatu"]))
                continue
            forms = []
            for p in derived:
                status = self.round_trip(p.text, want) if self.kosha is not None else "unchecked"
                if status == "mismatch":
                    violations.append(Violation("ROUND_TRIP_MISMATCH", p.text))
                forms.append({"text": p.text, "sutras": [s.code for s in p.history], "round_trip": status})
            out.append({**w, "forms": forms})
        if violations:
            return {"valid": False, "violations": [v.to_json() for v in violations]}
        return {"valid": True, "violations": [], "words": out,
                "text": " ".join(w["forms"][0]["text"] for w in out),
                "alternatives": [[f["text"] for f in w["forms"]] for w in out if len(w["forms"]) > 1]}
