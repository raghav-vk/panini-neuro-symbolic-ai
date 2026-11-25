# Texts in the Pretraining Corpora (Version 0.5)

The encoder was pretrained on **P-A**: every DCS_pick sentence (Krishna et al. 2017, CC BY 4.0) except the sandhi dev and test sentences and their copies. **P-B** also drops every sentence containing a held-out test word. Both are in SLP1. See `docs/PRETRAINING_PLAN.md` section 3.

DCS_pick does not record text names, so each sentence is matched by its letters against the DCS CoNLL-U treebank at its pinned commit (`datasets/dcs_conllu_manifest.json`; script `scripts/attribute_pretraining_texts.py`). {a['matched']:,} of {a['sentences']:,} P-A sentences (96.7%) matched a named text; the rest differ from the current DCS text, or are too short to match safely. A verse found in several texts is split equally between them (19,686 sentences).

P-A draws on **236 texts**, and P-B on 231. Their 40 largest, by share of the matched P-A sentences:

| # | Text | P-A sentences | Share | P-B sentences |
| ---: | --- | ---: | ---: | ---: |
| 1 | Mahābhārata | 122,380 | 28.8% | 100,272 |
| 2 | Rāmāyaṇa | 37,808 | 8.9% | 32,159 |
| 3 | Liṅgapurāṇa | 18,007 | 4.2% | 13,982 |
| 4 | Matsyapurāṇa | 17,442 | 4.1% | 13,681 |
| 5 | Skandapurāṇa (Revākhaṇḍa) | 16,023 | 3.8% | 13,529 |
| 6 | Suśrutasaṃhitā | 15,399 | 3.6% | 11,182 |
| 7 | Aṣṭāṅgahṛdayasaṃhitā | 14,774 | 3.5% | 11,210 |
| 8 | Kūrmapurāṇa | 12,037 | 2.8% | 9,378 |
| 9 | Ānandakanda | 11,968 | 2.8% | 9,262 |
| 10 | Garuḍapurāṇa | 10,321 | 2.4% | 8,184 |
| 11 | Bṛhatkathāślokasaṃgraha | 9,017 | 2.1% | 7,349 |
| 12 | Carakasaṃhitā | 8,134 | 1.9% | 5,830 |
| 13 | Rasaratnākara | 7,395 | 1.7% | 5,710 |
| 14 | Rājanighaṇṭu | 6,741 | 1.6% | 5,256 |
| 15 | Bhāgavatapurāṇa | 5,864 | 1.4% | 4,516 |
| 16 | Manusmṛti | 4,921 | 1.2% | 3,922 |
| 17 | Rasārṇava | 4,661 | 1.1% | 3,750 |
| 18 | Rasaratnasamuccaya | 3,834 | 0.9% | 2,946 |
| 19 | Hitopadeśa | 2,936 | 0.7% | 2,332 |
| 20 | Viṣṇusmṛti | 2,915 | 0.7% | 2,318 |
| 21 | Pañcārthabhāṣya | 2,823 | 0.7% | 2,104 |
| 22 | Āyurvedadīpikā | 2,796 | 0.7% | 1,999 |
| 23 | Rasendracūḍāmaṇi | 2,463 | 0.6% | 1,883 |
| 24 | Skandapurāṇa | 2,293 | 0.5% | 1,838 |
| 25 | Kāmasūtra | 2,257 | 0.5% | 1,776 |
| 26 | Mugdhāvabodhinī | 2,146 | 0.5% | 1,414 |
| 27 | Gokarṇapurāṇasāraḥ | 2,136 | 0.5% | 1,814 |
| 28 | Rasaprakāśasudhākara | 2,112 | 0.5% | 1,612 |
| 29 | Yājñavalkyasmṛti | 2,000 | 0.5% | 1,578 |
| 30 | Kātyāyanasmṛti | 1,954 | 0.5% | 1,666 |
| 31 | Buddhacarita | 1,953 | 0.5% | 1,529 |
| 32 | Nāradasmṛti | 1,847 | 0.4% | 1,528 |
| 33 | Bhāvaprakāśa | 1,824 | 0.4% | 1,435 |
| 34 | Bodhicaryāvatāra | 1,812 | 0.4% | 1,420 |
| 35 | Rasamañjarī | 1,736 | 0.4% | 1,349 |
| 36 | Rasendracintāmaṇi | 1,695 | 0.4% | 1,274 |
| 37 | Aṣṭādhyāyī | 1,622 | 0.4% | 1,481 |
| 38 | Śārṅgadharasaṃhitādīpikā | 1,558 | 0.4% | 1,187 |
| 39 | Mṛgendraṭīkā | 1,461 | 0.3% | 915 |
| 40 | Sātvatatantra | 1,375 | 0.3% | 1,090 |

The other 196 texts together hold 52,557 sentences (12.4%). The full list is in `corpus_texts.json`.

The stage 3 test (version 0.8) used only DCS chapters with no sentence in DCS_pick, so the encoder had not seen them (`docs/RLCD_TRANSITION_PLAN.md`, stage 3).
