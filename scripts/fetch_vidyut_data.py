#!/usr/bin/env python3
"""Download the pinned prebuilt Vidyut data release and verify it before unpacking.

The kosha mixes CC0 (learnsanskrit.org), LGPLLR (Sanskrit Heritage) and
CC BY-NC-SA 3.0 (Monier-Williams) material. It is a local research dependency:
never commit it or redistribute files derived from it.
"""

import argparse
import hashlib
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/ambuda-org/vidyut/releases/download/py-0.4.0/data-0.4.0.zip"
SHA256 = "5269cda86451a75dbc93b605f6864bb5a52cc79d66da02f18f30cf87d0059ecb"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "data/external/vidyut-0.4.0")
    args = p.parse_args()
    if (args.output / "kosha").exists():
        print(f"{args.output / 'kosha'} already exists")
        return
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / "data-0.4.0.zip"
    urllib.request.urlretrieve(URL, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != SHA256:
        archive.unlink()
        raise SystemExit(f"checksum mismatch: {digest}")
    with zipfile.ZipFile(archive) as z:
        root = args.output.resolve()
        for name in z.namelist():
            if not (args.output / name).resolve().is_relative_to(root):
                raise SystemExit(f"unsafe path in archive: {name}")
        z.extractall(args.output)
    archive.unlink()
    print(f"Verified and unpacked to {args.output}")


if __name__ == "__main__":
    main()
