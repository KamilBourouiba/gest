from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gest.sgm_decode import GestDecodeError
from gest.sgm_roundtrip import gest_document_from_sgm_bytes


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Decode .sgm v1 to a draft .gest JSON document (lossy recovery)."
    )
    p.add_argument("input", type=Path, help="Binary .sgm file")
    p.add_argument("output", type=Path, help="Output .json path")
    args = p.parse_args(argv)

    try:
        raw = args.input.read_bytes()
    except OSError as e:
        print(f"Cannot read file: {e}", file=sys.stderr)
        return 2

    try:
        doc = gest_document_from_sgm_bytes(raw)
    except GestDecodeError as e:
        print(f"Decode error: {e}", file=sys.stderr)
        return 1

    try:
        args.output.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"Cannot write file: {e}", file=sys.stderr)
        return 2

    print(f"Wrote draft .gest -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
