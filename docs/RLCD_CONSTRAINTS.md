# RLCD Constraint Layer: Review Request

**Status:** Draft, 2026-11-14. Nothing here has been reviewed. Part of stage 2
of `docs/RLCD_TRANSITION_PLAN.md` (protocol amendment 0.7, section 11.5).
**Reviewer:** the project grammarian.

## What This Is

The model proposes a clause as a small set of grammatical choices: root,
voice, tense, person, number, and its participants with their roles. Vidyut
then derives the Sanskrit. Vidyut derives a form for almost anything it is
given. It accepts karmaṇi of an intransitive root (`BUyate`), bhāve in the
dual (`BUyete`) and invented prefixes (`xygacCati`). So a constraint layer
decides first whether the choices are licit, and nothing is derived if they
are not.

Vidyut does refuse a pada the root does not take: *labh* in parasmaipada
derives nothing. The layer reports this as `NO_DERIVATION`.

**Please review three things:** the checks and their sūtra basis (section 1),
the root table (section 2) and the stem table (section 3). For each row, mark
it agreed, corrected or rejected, with a note. A GitHub issue or comments on
the pull request both work.

## 1. Checks

The code is `src/panini/clause.py`. The sūtra references are our draft basis;
please correct them.

| Code | Rule as implemented | Draft basis |
| --- | --- | --- |
| `DHATU_UNKNOWN` | Root, gaṇa and code must be one Dhātupāṭha entry | Dhātupāṭha (Vidyut `dhatupatha.tsv`) |
| `KARMAKATVA_UNKNOWN` | The root, with exactly these upasargas, must be in the root table | — |
| `KARMANI_NEEDS_SAKARMAKA` | Karmaṇi needs a sakarmaka root | 3.4.69 *laḥ karmaṇi ca bhāve cākarmakebhyaḥ* |
| `BHAVE_NEEDS_AKARMAKA` | Bhāve needs an akarmaka root | 3.4.69 |
| `BHAVE_FORM` | A bhāve verb is prathama puruṣa, ekavacana | 1.4.22, 1.4.108? |
| `BHAVE_NO_KARMAN` | Bhāve has no karman | 3.4.69 |
| `KARMAN_NEEDS_SAKARMAKA` | An akarmaka root takes no karman | 1.4.49? |
| `ROLE_COUNT` | Each role at most once | Simplification of v0.3 |
| `AGREEMENT_MISSING` | Kartari needs a kartṛ and karmaṇi a karman, the participant the verb agrees with | Simplification: no ellipsis in v0.3 |
| `AGREEMENT_PURUSHA` | Verb puruṣa = the agreeing participant's: *asmad* uttama, *yuṣmad* madhyama, otherwise prathama | 1.4.105, 1.4.107, 1.4.108 |
| `AGREEMENT_VACANA` | Verb vacana = the agreeing participant's | 1.4.21, 1.4.22 |
| `STEM_UNKNOWN`, `LINGA_MISMATCH` | Stem and gender must be in the stem table | — |
| `ENGINE_DEFECT` | Bhāve luṅ is blocked: Vidyut 0.4.0 omits ciṇ there (`aBAvizwa` for *aBāvi*, `asTita` for *asthāyi*), though it applies ciṇ in karmaṇi (`agAmi`) | 3.1.66 *ciṇ bhāvakarmaṇoḥ*; please confirm the expected forms |

Cases assigned by role, after the checks pass:

| Role | Kartari | Karmaṇi | Bhāve | Draft basis |
| --- | --- | --- | --- | --- |
| kartṛ | prathamā | tṛtīyā | tṛtīyā | 2.3.46 (abhihita); 2.3.18 |
| karman | dvitīyā | prathamā | — | 2.3.2; 2.3.46 (abhihita) |
| karaṇa | tṛtīyā | tṛtīyā | tṛtīyā | 2.3.18 |
| adhikaraṇa | saptamī | saptamī | saptamī | 2.3.36 |

**Known simplifications in v0.3.** Please say which matter most to lift first:

1. Only unprefixed roots are in the root table. Upasargas can change
   transitivity (*adhi-vas*, 1.4.48), so prefixed roots are rejected until
   rows for them are added.
2. Dvikarmaka use (*ajāṃ grāmaṃ nayati*, 1.4.51) is not modelled.
3. Akarmaka roots with a karman of time, place, way or state (*māsam āste*)
   are rejected.
4. Ellipsis is not modelled: the agreeing participant must be present.
5. Words are pausal. External sandhi between words is not applied.

## 2. Root Table (`data/rlcd/dhatu_constraints.tsv`)

There are 31 roots. Each row's code, root and gaṇa are checked against the
Dhātupāṭha by test. The column to review is **karmakatva**: sakarmaka or
akarmaka, for the meaning given. Notes flag cases we were unsure of, such as
*pat* and *kruḍh*.

## 3. Stem Table (`data/rlcd/stem_lexicon.tsv`)

There are 39 stems. The columns to review are **lingas**, the genders the stem
takes, and **kind**: `nyap` for stems ending in a feminine suffix, which
decline differently (*sītā* → *sītayā*).

Gender comes from this table, not from the Vidyut kosha. The kosha inflects
stems in every gender (it lists *aśvā* as a feminine form of *aśva*), so it
cannot say which genders a stem takes. Its stem-level gender list is
incomplete as well: it gives *jala* and *pustaka* as masculine only.

## How Results Are Checked

`data/rlcd/clause_fixtures.jsonl` holds 30 hand-written cases: 12 licit
clauses with their expected forms, and 18 illicit ones with the violation
each must raise. The tests run them through the pure layer and through
Vidyut. Every derived form carries its sūtra steps. Of the 36 forms derived
from the licit cases, the kosha confirms 35. The exception, *patram*, is not
in the kosha and is reported, not rejected.
