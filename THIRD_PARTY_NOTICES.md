# Third-Party Data Notices

Project code and original documentation use the repository's Apache-2.0
license. Third-party datasets retain their own terms and are not relicensed
under Apache-2.0.

## DCS_pick

`datasets/DCS_pick.zip` is the `DCS_pick.zip` artifact from:

> Amrith Krishna, Pavankumar Satuluri, and Pawan Goyal. 2017. *A Dataset
> for Sanskrit Word Segmentation*. Zenodo. DOI: 10.5281/zenodo.803508.

Zenodo identifies the record as Creative Commons Attribution 4.0
International (CC BY 4.0). The local archive matches Zenodo's filename, size,
and MD5. See `datasets/dcs_source_manifest.json` for the complete checksums and
attribution record.

License: https://creativecommons.org/licenses/by/4.0/

## ashtadhyayi-com/data

The all-sandhi source-candidate corpus was generated from
`sutraani/data.txt` at commit:

    51bff9fb38c6f571b4a2bc8499d97576f00ffcce

Repository: https://github.com/ashtadhyayi-com/data

### Terms of use

The pinned snapshot contains no `LICENSE`, `NOTICE`, or `COPYING` file. The
terms below come from a written reply by the ashtadhyayi.com maintainer,
Neelesh Bodas, to the project author on 18 February 2024:

> This data is available for use as long as the product generated from this
> data is made available for free for others. Commercial use of the dataset
> is not allowed.

These terms are stricter than Apache-2.0, which permits commercial use.
Therefore:

- Artifacts derived from this source, including
  `data/sources/ashtadhyayi_sandhi_sutras.jsonl` and the sūtra identifiers
  and text copied into `data/rules/development_sandhi.jsonl`, are provided
  free of charge under the upstream terms above, not under Apache-2.0.
- Do not use those artifacts, or products generated from them, commercially.
- The generated corpus contains only sūtra identifiers, ancient sūtra text,
  factual classification fields, and provenance. It omits modern commentary
  and translations.

Anyone redistributing these artifacts must keep this notice with them.

## Vidyut kosha (optional external lexicon)

`scripts/fetch_vidyut_data.py` downloads the prebuilt Vidyut 0.4.0 data
release into `data/external/` (gitignored) and verifies its SHA-256:

    https://github.com/ambuda-org/vidyut/releases/download/py-0.4.0/data-0.4.0.zip

Vidyut's code is MIT licensed (https://github.com/ambuda-org/vidyut). Its
kosha (word list) is built from `sanskrit/data`
(https://github.com/sanskrit/data), whose sources carry their own terms:

- learnsanskrit.org: CC0 1.0 (public domain).
- Sanskrit Heritage Site: Lesser General Public License for Linguistic
  Resources.
- Monier-Williams dictionary: CC BY-NC-SA 3.0. Non-commercial; derivative
  works must use the same license.

The kosha is used only as a local research dependency, through the
`--external-lexicon` ranker option. The kosha and the `kosha_left` and
`kosha_right` flags derived from it are not committed or redistributed.
Checkpoints trained with that option record only learned feature weights and
training-split counts, but should be treated as covered by the
non-commercial, share-alike terms above. Do not use them commercially.
