from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gest.document import load_path
from gest.sgm import GestCompileError, compile_to_bytes
from gest.validate import validate_all


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Compile a .gest file (JSON or YAML) to .sgm v1 bytecode."
    )
    p.add_argument("input", type=Path, help="Source .json / .yaml / .yml")
    p.add_argument("output", type=Path, help="Binary .sgm output path")
    p.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validate_all (schema + invariants).",
    )
    args = p.parse_args(argv)

    try:
        doc = load_path(args.input)
    except ImportError as e:
        print(str(e), file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print(f"Cannot load document: {e}", file=sys.stderr)
        return 2

    if not args.no_validate:
        errs = validate_all(doc)
        sch = [e for e in errs if not e.startswith("invariant:")]
        inv = [e for e in errs if e.startswith("invariant:")]
        fail = False
        if sch:
            only_missing = len(sch) == 1 and sch[0].startswith("jsonschema")
            if not only_missing:
                for line in sch:
                    print(line, file=sys.stderr)
                fail = True
            else:
                print(sch[0], file=sys.stderr)
        if inv:
            for line in inv:
                print(line, file=sys.stderr)
            fail = True
        if fail:
            return 1

    try:
        blob = compile_to_bytes(doc)
    except GestCompileError as e:
        print(f"Compile error: {e}", file=sys.stderr)
        return 1

    try:
        args.output.write_bytes(blob)
    except OSError as e:
        print(f"Cannot write output: {e}", file=sys.stderr)
        return 2

    print(f"Wrote {len(blob)} bytes -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
