# RLCD Stage 3: Frozen Test Run (generated; stage 3 test part)

Amendment 0.8 (protocol section 11.6, docs/STAGE3_TEST_AMENDMENT.md). Code at commit `6367e00773b5d0f87f9237e0a2980fef553f5612`. 133,107 words in 167 chapters (71 without a form dropped); 47,089 outside Kathāsaritsāgara; 9,446 with forms unseen in training. Intervals: 95% chapter bootstrap.

## Confirmatory hypotheses

- **T-1** N1 beats N2 on full-tag accuracy: per seed +0.0629, +0.0612, +0.0597; mean +0.0613 [+0.0578, +0.0644]; **supported**
- **T-2** N1 beats B2 on full-tag accuracy, pooled: per seed +0.0207, +0.0166, +0.0174; mean +0.0182 [-0.0052, +0.0403]; **not supported**
- **T-2b** B2 beats N1 outside Kathasaritsagara (difference B2 - N1): per seed +0.0356, +0.0394, +0.0371; mean +0.0374 [-0.0183, +0.0813]; **not supported**
- **T-3** frozen J4 has lower NLL than J0 (difference J4 - J0): per seed -0.0042, -0.0034, -0.0037; mean -0.0038 [-0.0058, -0.0020]; **supported**
- **T-4** test coverage at the frozen tau lies within [0.85, 0.95] for every seed: coverage 0.886, 0.884, 0.885; **supported**

## Systems

| System | Role | Full tag | Unseen forms | vibhakti | vacana | liṅga | puruṣa | lakāra |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B2 | baseline | 0.862 [0.857, 0.866] | 0.485 [0.467, 0.506] | 0.864 | 0.946 | 0.852 | 0.950 | 0.948 |
| N1-seed7 | confirmatory | 0.882 [0.859, 0.905] | 0.768 [0.716, 0.818] | 0.912 | 0.955 | 0.876 | 0.942 | 0.925 |
| N1-seed11 | confirmatory | 0.878 [0.854, 0.902] | 0.760 [0.710, 0.809] | 0.910 | 0.954 | 0.871 | 0.939 | 0.917 |
| N1-seed19 | confirmatory | 0.879 [0.856, 0.901] | 0.761 [0.710, 0.811] | 0.910 | 0.953 | 0.872 | 0.937 | 0.918 |
| N2-seed7 | confirmatory | 0.819 [0.796, 0.841] | 0.701 [0.649, 0.751] | 0.874 | 0.929 | 0.814 | 0.862 | 0.835 |
| N2-seed11 | confirmatory | 0.817 [0.793, 0.840] | 0.696 [0.644, 0.747] | 0.872 | 0.928 | 0.813 | 0.865 | 0.836 |
| N2-seed19 | confirmatory | 0.819 [0.796, 0.841] | 0.695 [0.643, 0.746] | 0.874 | 0.930 | 0.815 | 0.866 | 0.836 |
| N3-seed7 | descriptive | 0.878 [0.854, 0.901] | 0.767 [0.715, 0.816] | 0.909 | 0.953 | 0.874 | 0.923 | 0.899 |
| N3-seed11 | descriptive | 0.875 [0.852, 0.898] | 0.758 [0.708, 0.806] | 0.907 | 0.952 | 0.871 | 0.917 | 0.895 |
| N3-seed19 | descriptive | 0.876 [0.852, 0.898] | 0.757 [0.707, 0.807] | 0.907 | 0.951 | 0.870 | 0.916 | 0.895 |

## Calibration and gate (N1; N3 descriptive)

| Run | Calibrator | NLL | ECE | Mean conf. / accuracy | Gate coverage | Accepted full tag |
| --- | --- | --- | --- | --- | --- | --- |
| N1-seed7 | J0 | 0.2116 | 0.0204 | 0.874 / 0.882 | — | — |
| N1-seed7 | J4 | 0.2073 | 0.0059 | 0.879 / 0.882 | 0.886 | 0.942 |
| N1-seed11 | J0 | 0.2156 | 0.0189 | 0.871 / 0.878 | — | — |
| N1-seed11 | J4 | 0.2122 | 0.0065 | 0.874 / 0.878 | 0.884 | 0.939 |
| N1-seed19 | J0 | 0.2165 | 0.0203 | 0.871 / 0.879 | — | — |
| N1-seed19 | J4 | 0.2128 | 0.0076 | 0.874 / 0.879 | 0.885 | 0.939 |
| N2-seed7 | J0 | 0.3012 | 0.0280 | 0.792 / 0.819 | — | — |
| N2-seed11 | J0 | 0.3004 | 0.0288 | 0.789 / 0.817 | — | — |
| N2-seed19 | J0 | 0.3009 | 0.0283 | 0.791 / 0.819 | — | — |
| N3-seed7 | J0 | 0.2245 | 0.0209 | 0.868 / 0.878 | — | — |
| N3-seed11 | J0 | 0.2275 | 0.0194 | 0.867 / 0.875 | — | — |
| N3-seed19 | J0 | 0.2300 | 0.0211 | 0.866 / 0.876 | — | — |

## Per text (N1 seed 7 against B2)

| Text | Words | N1 seed 7 | B2 |
| --- | ---: | ---: | ---: |
| Kathāsaritsāgara | 86,018 | 0.914 | 0.862 |
| Harṣacarita | 12,305 | 0.694 | 0.860 |
| Kirātārjunīya | 9,336 | 0.867 | 0.841 |
| Tantrāloka | 5,741 | 0.915 | 0.886 |
| Mīmāṃsāsūtrabhāṣya | 3,669 | 0.867 | 0.892 |
| Śatakatraya | 2,511 | 0.800 | 0.855 |
| Nāṭyaśāstra | 2,233 | 0.922 | 0.820 |
| Śyainikaśāstra | 2,101 | 0.919 | 0.873 |
| Mūlamadhyamakārikāḥ | 1,514 | 0.911 | 0.884 |
| Lalitavistara | 1,447 | 0.738 | 0.873 |
| Śukasaptati | 1,063 | 0.874 | 0.889 |
| Abhidhānacintāmaṇi | 1,029 | 0.924 | 0.873 |
| Aṣṭādhyāyī | 982 | 0.787 | 0.742 |
| Harivaṃśa | 805 | 0.902 | 0.882 |
| Avadānaśataka | 643 | 0.781 | 0.877 |
| Rājanighaṇṭu | 459 | 0.895 | 0.824 |
| Nibandhasaṃgraha | 296 | 0.821 | 0.936 |
| Kauśikasūtradārilabhāṣya | 266 | 0.880 | 0.820 |
| Yogasūtrabhāṣya | 223 | 0.785 | 0.888 |
| Kauśikasūtrakeśavapaddhati | 222 | 0.734 | 0.712 |
| Nyāyabindu | 115 | 0.939 | 0.922 |
| Ratnaṭīkā | 71 | 0.831 | 0.986 |
| Kāśikāvṛtti | 48 | 0.792 | 0.917 |
| Rasaratnasamuccayabodhinī | 5 | 0.600 | 0.400 |
| Rasaratnasamuccayaṭīkā | 5 | 1.000 | 1.000 |
