"""Validate explicitly named generator exports with the installed Hard-CAD SDK.

Example (after generate_demo.py):
  python examples/validator/run_generator_pipeline.py --models demo-models \
      --candidate before=before.step --candidate after=after.step \
      --contract examples/validator/contract.json \
      --reference demo-models/reference.step --output demo-batch \
      --cad-python FREECAD_PYTHON

The input names and contract come from the caller; this example neither reads
prompts nor guesses dimensions or design intent from CAD filenames.
"""
from __future__ import annotations

import argparse
import json

from hardcad.batch import BatchError, run_batch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", required=True, help="Base directory for the listed candidate files")
    parser.add_argument("--candidate", action="append", required=True, metavar="ID=RELATIVE_STEP",
                        help="Repeat for each explicitly named generator output")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--reference", help="Optional explicit STEP/BREP reference")
    parser.add_argument("--output", required=True, help="New report directory")
    parser.add_argument("--cad-python", required=True, help="FreeCAD-capable Python interpreter")
    args = parser.parse_args()
    candidates = []
    for text in args.candidate:
        if "=" not in text:
            parser.error("--candidate must be ID=RELATIVE_STEP")
        identifier, relative = text.split("=", 1)
        candidates.append({"id": identifier, "path": relative})
    manifest = {"schema_version": "hardcad.batch.v1", "candidates": candidates}
    try:
        result = run_batch(manifest, args.contract, reference=args.reference,
                           cad_python=args.cad_python, base_dir=args.models,
                           output_dir=args.output)
    except (BatchError, OSError, ValueError) as exc:
        parser.exit(2, f"hardcad batch: {exc}\n")
    print(json.dumps(result["index"], ensure_ascii=False, sort_keys=True, indent=2))
    return {"PASS": 0, "FAIL": 1, "ERROR": 2, "UNDETERMINED": 3}[result["index"]["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
