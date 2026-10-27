"""Embed the deployable files in a standalone EC2 user-data shell script.

Run: python tools/build_user_data.py
Check that the committed script is up to date: python tools/build_user_data.py --check
No third-party Python packages are needed for this helper.
"""

import argparse
import base64
import gzip
import io
from pathlib import Path
import tarfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deploy" / "user-data.sh"
DEPLOY_FILES = (
    "app.py", "menu.py", "requirements.txt", "templates/index.html",
    "static/style.css", "static/script.js", "static/cafe.svg",
    "deploy/cloud-cafe.service", "deploy/deploy.sh",
)


def build_script():
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
        for name in DEPLOY_FILES:
            # Read as text to normalize Windows line endings to Linux line endings.
            data = (ROOT / name).read_text(encoding="utf-8").encode("utf-8")
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            bundle.addfile(member, io.BytesIO(data))
    encoded = base64.b64encode(gzip.compress(archive.getvalue(), mtime=0)).decode("ascii")
    payload = "\n".join(textwrap.wrap(encoded, width=76))
    script = f"""#!/bin/bash
# Cloud Cafe standalone user data for Ubuntu 22.04 or 26.04 LTS.
# Generated from project files by tools/build_user_data.py; do not edit the payload.
# No repository or AWS credentials needed. Package installation needs internet.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
    echo "Run this script as root (EC2 user data already does this)." >&2
    exit 1
fi
STAGING_DIR=/var/lib/cloud-cafe/source
install -d -o root -g root -m 0755 "$STAGING_DIR"
# The base64 text below contains a compressed archive of the actual project.
base64 --decode <<'CLOUD_CAFE_PAYLOAD' | tar -xzf - -C "$STAGING_DIR" --no-same-owner
{payload}
CLOUD_CAFE_PAYLOAD
bash "$STAGING_DIR/deploy/deploy.sh"
"""
    if len(script.encode("utf-8")) > 16_384:
        raise ValueError("The script exceeds EC2's 16 KiB unencoded user-data limit.")
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build_script()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != expected.encode("utf-8"):
            parser.exit(1, "user-data.sh is stale. Run python tools/build_user_data.py\n")
        print(f"User data matches the project ({len(expected.encode('utf-8'))} / 16384 bytes).")
    else:
        OUTPUT.write_bytes(expected.encode("utf-8"))
        print(f"Wrote {OUTPUT} ({len(expected.encode('utf-8'))} / 16384 bytes).")


if __name__ == "__main__":
    main()
