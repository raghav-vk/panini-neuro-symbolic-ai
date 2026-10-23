# Development Experiment Results

Data: **synthetic_engineering_smoke**. Not evidence of Sanskrit accuracy or contextual understanding.

| Split | Model | Seeds | Mean top-1 | SD | Candidate recall |
|---|---|---:|---:|---:|---:|
| source_random | symbolic_order | 1 | 0.6573 | 0.0000 | 1.0000 |
| source_random | frequency | 1 | 0.6895 | 0.0000 | 1.0000 |
| source_random | character_bigram | 1 | 0.6694 | 0.0000 | 1.0000 |
| source_random | tiny_full | 5 | 0.6815 | 0.0103 | 1.0000 |
| source_random | tiny_no_rules | 5 | 0.6710 | 0.0160 | 1.0000 |
| source_random | tiny_no_context | 5 | 0.6815 | 0.0103 | 1.0000 |
| pair | symbolic_order | 1 | 0.6573 | 0.0000 | 1.0000 |
| pair | frequency | 1 | 0.6895 | 0.0000 | 1.0000 |
| pair | character_bigram | 1 | 0.6694 | 0.0000 | 1.0000 |
| pair | tiny_full | 5 | 0.6815 | 0.0103 | 1.0000 |
| pair | tiny_no_rules | 5 | 0.6710 | 0.0160 | 1.0000 |
| pair | tiny_no_context | 5 | 0.6815 | 0.0103 | 1.0000 |
| strict_lemma | symbolic_order | 1 | 0.6107 | 0.0000 | 1.0000 |
| strict_lemma | frequency | 1 | 0.6107 | 0.0000 | 1.0000 |
| strict_lemma | character_bigram | 1 | 0.6489 | 0.0000 | 1.0000 |
| strict_lemma | tiny_full | 5 | 0.6687 | 0.0391 | 1.0000 |
| strict_lemma | tiny_no_rules | 5 | 0.6763 | 0.0278 | 1.0000 |
| strict_lemma | tiny_no_context | 5 | 0.6687 | 0.0391 | 1.0000 |

Coverage is circular on generator-derived probes. Empty synthetic contexts cannot establish contextual gains.
Source-random and pair splits may coincide when source groups already identify pairs. Strict mixed rows remain excluded and counted.
Hyperparameters fixed before test; epoch and abstention threshold selected on dev only. Test is not used for training.
Intervals in JSON are itemwise Wilson intervals, not source-cluster bootstrap intervals. RSS is cumulative process peak, not model-only memory.
No unconstrained generative baseline or independently reviewed Sanskrit benchmark is claimed by this smoke experiment.

## Conversion and Resources

DCS: 441,735 examined; 441,722 converted; 13 quarantined. 200 initial review proposals; none expert reviewed.

Tiny ranker: 128,769 parameters on CPU. 45 neural fits across holdouts, seeds and variants.
Fit times including development evaluation: 1.06 to 3.50 seconds per fit.
Maximum cumulative process RSS: 319.5 MiB. This is not isolated model memory.

Raw checkpoints and item predictions remain under the original run directory, excluded from Git. JSON metrics, corpus rejection reasons and code hashes are retained here.
Do not substitute these probe scores for the manuscript's planned independent-corpus results.
