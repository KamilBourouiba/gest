from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gest.document import load_path
from gest.validate import validate_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a .gest file (JSON or YAML): schema + IR invariants."
    )
    parser.add_argument("path", type=Path, help="Path to .json, .yaml, or .yml")
    args = parser.parse_args(argv)

    try:
        doc = load_path(args.path)
    except ImportError as e:
        print(str(e), file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"Cannot read file: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    errors = validate_all(doc)
    sch = [e for e in errors if not e.startswith("invariant:")]
    inv = [e for e in errors if e.startswith("invariant:")]
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

    print("OK: gest-0.2 schema + invariants.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
