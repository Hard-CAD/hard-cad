"""Verify public entity-screen receipts; do not access original DOCX or STEP."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FROZEN = {
    "data/document_entity_candidate_protocol.json": "bd3e6c2b03fcc3a409db3f38e08e3d37ff484ab612f509de13564a4fbc01511e",
    "results/document_entity_candidates.json": "de3ec85e5712d312bf1b038a20cf84e5a6e295a7522beef488fe179e7311673a",
}


def _check_files(root, expected, checked):
    for name, digest in expected.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Receipt source escapes repository root")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("Frozen artifact hash mismatch: " + name)
        checked[name] = actual


def verify(root=ROOT):
    root = Path(root)
    checked = {}
    _check_files(root, FROZEN, checked)
    protocol = json.loads((root / "data/document_entity_candidate_protocol.json").read_text(encoding="utf-8"))
    result = json.loads((root / "results/document_entity_candidates.json").read_text(encoding="utf-8"))
    _check_files(root, protocol["upstream"], checked)
    _check_files(root, {"tools/audit_document_entity_candidates.py": result["implementation_sha256"]}, checked)
    if result["protocol_sha256"] != checked["data/document_entity_candidate_protocol.json"]:
        raise ValueError("Recorded protocol identity differs")
    fields = tuple(protocol["cases"][0])
    if [{key: row[key] for key in fields} for row in result["rows"]] != protocol["cases"]:
        raise ValueError("Recorded source cohort differs")

    from tools import audit_document_entity_candidates as screen

    if protocol["bands"] != screen.BANDS or protocol["permutations"] != [list(item) for item in screen.PERMUTATIONS]:
        raise ValueError("Numerical screening rules differ")
    summary = screen.summarize(result["rows"])
    if summary != result["summary"]:
        raise ValueError("Recorded summary differs from row aggregates")
    return {"status": "VERIFIED_PUBLIC_RECEIPTS", "new_geometry_measurements": 0,
            "new_model_calls": 0, "private_artifacts_verified": False,
            "verified_public_artifacts": len(checked), "summary": summary,
            "binding_qualification": result["binding_qualification"],
            "scope": "Solid bounding-box and literal-name screening; candidate counts are not semantic precision/recall."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional new JSON file; parent must exist")
    args = parser.parse_args(argv)
    try:
        payload = json.dumps(verify(), indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
        print(payload, end="")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc) if isinstance(exc, ValueError) else type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
