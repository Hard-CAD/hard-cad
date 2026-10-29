"""Verify public receipts and recompute aggregates; no inference or CAD replay."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# These anchors identify this recorded experiment, rather than accepting a
# mutually edited protocol and result as the original experiment.
FROZEN = {
    "data/binding_proposal_protocol.json": "1e8971e6177ae9ae8d67aa0d7d4a1c39d65d04cd1cfb197dde44f9cfdaa1d5e6",
    "data/binding_decoding_protocol.json": "74af5cbe9796d8d2d7a86e4b97b8e9384c51ee48ce64221d9a69fe7b8b2efefa",
    "data/binding_propagation_protocol.json": "14147890b0f986419280d89c89680b8de00b9a0b117475fd011393d36d9a75c8",
    "results/binding_proposal_pilot.json": "a489c378ef4ecc695a424b4c441cea4933feb14af0ba4cfd6782930df301a7f0",
    "results/binding_decoding_sensitivity.json": "b2bfe3294478a140b2de83055c24880c8a40732654ac9d888ae3fc8cb592a2f8",
    "results/binding_propagation.json": "35633e64463861df96601b3aaf55e3e26b9fd36fc68560f8e94b9d0e48c30600",
    "results/binding_propagation_decoded.json": "1bf1a8739ff398d0a3d7431d8763d5a05602bbd5412acc97737483fe061046ad",
}


def _read(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def _check_files(root, expected, checked):
    for name, digest in expected.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Receipt source escapes repository root")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("Frozen artifact hash mismatch: " + name)
        checked[name] = actual


def _require_equal(actual, expected, label):
    if actual != expected:
        raise ValueError("Recorded evidence mismatch: " + label)


def verify(root=ROOT):
    """Read only public artifacts; return an independently recomputed summary."""
    root = Path(root)
    checked = {}
    _check_files(root, FROZEN, checked)
    proposal = _read(root, "data/binding_proposal_protocol.json")
    decoding = _read(root, "data/binding_decoding_protocol.json")
    propagation = _read(root, "data/binding_propagation_protocol.json")
    strict = _read(root, "results/binding_proposal_pilot.json")
    decoded = _read(root, "results/binding_decoding_sensitivity.json")
    _check_files(root, proposal["input_sha256"], checked)
    _check_files(root, propagation["source_sha256"], checked)
    _check_files(root, {"tools/run_binding_proposal_pilot.py": proposal["runner_sha256"],
                        "tools/decode_binding_proposals.py": decoding["decoder_sha256"]}, checked)
    _require_equal(strict["protocol_sha256"], checked["data/binding_proposal_protocol.json"], "strict protocol")
    _require_equal(decoded["protocol_sha256"], checked["data/binding_decoding_protocol.json"], "decoding protocol")
    _require_equal(decoding["primary_result_sha256"], checked["results/binding_proposal_pilot.json"], "primary result")
    _require_equal(decoding["primary_protocol_sha256"], checked["data/binding_proposal_protocol.json"], "primary protocol")
    _require_equal(decoding["source_sha256"], checked["data/cad_agent_cases.json"], "recipe source")

    from tools import run_binding_proposal_pilot as pilot
    from tools import measure_binding_propagation as downstream

    cases = _read(root, "data/cad_agent_cases.json")["cases"]
    _require_equal(proposal["order"], [case["case_id"] for case in cases], "allocated brief order")
    _require_equal(proposal["model_parameters"], pilot.PARAMETERS, "model parameters")
    _require_equal(proposal["gold_source_digest"], pilot.digest({case["case_id"]: pilot.gold(case) for case in cases}), "recipe targets")
    _require_equal(proposal["prompts"], [{"case_id": case["case_id"], "messages_sha256": pilot.digest(pilot.messages(case))} for case in cases], "prompt rendering")
    for report, name in ((strict, "strict"), (decoded, "decoded")):
        _require_equal([row["case_id"] for row in report["rows"]], proposal["order"], name + " row order")
        for field, target in (("symbolic", "symbolic"), ("geometry", "geometric")):
            _require_equal(pilot.aggregate(report["rows"], field), report[target], name + " " + target)
    _require_equal([{"case_id": row["case_id"], "messages_sha256": row["prompt_sha256"]} for row in strict["rows"]], proposal["prompts"], "captured prompt identities")
    _require_equal([{"case_id": row["case_id"], "raw_response_sha256": row["raw_response_sha256"],
                     "primary_receipt_sha256": row["receipt_sha256"]} for row in strict["rows"]], decoding["rows"], "decoder input identities")
    _require_equal([(row["case_id"], row["raw_response_sha256"]) for row in strict["rows"]],
                   [(row["case_id"], row["raw_response_sha256"]) for row in decoded["rows"]], "same captured responses")
    exact = lambda rows: sum(row["symbolic"] is not None and row["symbolic"]["fp"] == row["symbolic"]["fn"] == 0 for row in rows)
    strict_counts = {"allocated_cases": len(strict["rows"]),
                     "calls": sum(row["status"] != "NOT_ATTEMPTED" for row in strict["rows"]),
                     "gold_operations": sum(row["gold_count"] for row in strict["rows"]),
                     "statuses": dict(Counter(row["status"] for row in strict["rows"])),
                     "exact_case_successes": exact(strict["rows"]), "new_natural_documents": 0}
    decoded_counts = {"allocated_cases": len(decoded["rows"]),
                      "decoded": sum(row["status"] == "DECODED" for row in decoded["rows"]),
                      "outer_fence_removed": sum(row["decoding"] == "OUTER_FENCE_REMOVED" for row in decoded["rows"]),
                      "exact_case_successes": exact(decoded["rows"])}
    _require_equal(strict_counts, strict["counts"], "strict counts")
    _require_equal(decoded_counts, decoded["counts"], "decoded counts")
    _require_equal(decoded["new_model_calls"], 0, "post-hoc model calls")

    summaries = {}
    for mode, name in (("strict", "results/binding_propagation.json"),
                       ("outer-fence", "results/binding_propagation_decoded.json")):
        report = _read(root, name)
        _check_files(root, report["sources"], checked)
        _require_equal(report["decoding"], mode, "propagation mode")
        _require_equal([{**{key: row[key] for key in ("case_id", "model", "attempt_index")},
                         "status": row["archived_status"]} for row in report["rows"]],
                       propagation["endpoints"], "propagation allocations")
        summary = downstream.summarize(report["rows"])
        _require_equal(summary, report["summary"], "propagation aggregates")
        summaries[mode] = {key: summary[key] for key in (
            "endpoint_allocations", "matched_requirement_verdict_agreement",
            "all_eligible_original_positive_requirement_instances",
            "unavailable_positive_requirement_instances", "no_cut_endpoints", "status_counts")}

    return {"status": "VERIFIED_PUBLIC_RECEIPTS", "new_model_calls": 0,
            "new_geometry_measurements": 0, "private_artifacts_verified": False,
            "verified_public_artifacts": len(checked),
            "strict": {"counts": strict_counts, "symbolic": strict["symbolic"]},
            "post_hoc_outer_fence": {"counts": decoded_counts, "symbolic": decoded["symbolic"], "new_model_calls": 0},
            "propagation": summaries,
            "scope": "Controlled template briefs and recorded endpoint measurements; not natural-document extraction accuracy."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional new JSON file; parent must exist")
    args = parser.parse_args(argv)
    try:
        report = verify()
        payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
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
