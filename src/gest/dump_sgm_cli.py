from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from gest.sgm_decode import GestDecodeError, decode_sgm_bytes, decoded_to_pose_timeline


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Decode a .sgm v1 file to JSON (channel table + reconstructed timeline)."
    )
    p.add_argument("input", type=Path, help="Binary .sgm file")
    args = p.parse_args(argv)

    try:
        raw = args.input.read_bytes()
    except OSError as e:
        print(f"Cannot read file: {e}", file=sys.stderr)
        return 2

    try:
        decoded = decode_sgm_bytes(raw)
    except GestDecodeError as e:
        print(f"Decode error: {e}", file=sys.stderr)
        return 1

    out = {
        "format_version": decoded.format_version,
        "fps": decoded.fps,
        "channels": [asdict(c) for c in decoded.channels],
        "timeline": decoded_to_pose_timeline(decoded),
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
