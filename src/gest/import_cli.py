from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gest.importers import bvh_text_to_gest, mediapipe_json_to_gest, openxr_json_to_gest
from gest.validate import validate_all


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input JSON root must be an object.")
    return data


def _write_doc(doc: dict, output: Path) -> None:
    output.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _validate(doc: dict) -> list[str]:
    return [e for e in validate_all(doc) if not e.startswith("jsonschema")]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Import external motion captures into .gest JSON.")
    sub = p.add_subparsers(dest="kind", required=True)

    for name in ("mediapipe", "openxr", "bvh"):
        sp = sub.add_parser(name, help=f"Import {name} input")
        sp.add_argument("input", type=Path)
        sp.add_argument("output", type=Path)
        if name == "bvh":
            sp.add_argument("--fps", type=float, default=None, help="Override BVH frame-time FPS")

    args = p.parse_args(argv)

    try:
        if args.kind == "mediapipe":
            doc = mediapipe_json_to_gest(_load_json(args.input))
        elif args.kind == "openxr":
            doc = openxr_json_to_gest(_load_json(args.input))
        elif args.kind == "bvh":
            doc = bvh_text_to_gest(args.input.read_text(encoding="utf-8"), fps=args.fps)
        else:
            raise ValueError(f"Unknown importer: {args.kind}")
        errors = _validate(doc)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        _write_doc(doc, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"Import failed: {e}", file=sys.stderr)
        return 2

    print(f"Wrote .gest -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

