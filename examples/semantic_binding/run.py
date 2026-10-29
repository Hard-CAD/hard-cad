"""Run real learned retrieval and an independent exact geometric check."""
from __future__ import annotations

import argparse
import base64
from html import escape
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from hardcad import bind_dimension, diagnose
from hardcad.binding_cli import _html
from hardcad.contracts import contract_sha256, validate_contract
from hardcad.report import Report


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def fixture_mapping(inventory):
    """Bind the original demonstration placements, independent of STEP order."""
    mapping = {}
    rows = inventory["rows"]
    if len(rows) != 3 or any(row["status"] != "RENDERED" for row in rows):
        raise ValueError("Demo requires exactly three rendered solids")
    for name, offset in (("through", 0), ("blind", 50), ("solid", 100)):
        expected = [offset, 0, 0, offset + 36, 24, 6]
        matches = [row for row in rows if len(row["bounds_mm"]) == 6 and
                   all(abs(a - b) <= 1e-5 for a, b in zip(row["bounds_mm"], expected))]
        if len(matches) != 1:
            raise ValueError("Demo solid placement cannot be uniquely verified: " + name)
        mapping[name] = matches[0]["id"]
    if len(set(mapping.values())) != 3:
        raise ValueError("Demo placements do not identify distinct solids")
    return mapping


def feedback_record(name, report, contract):
    """Retain the exact checked predicate; do not infer a semantic error label."""
    data = Report(report).to_dict()
    contract = validate_contract(contract)
    if data["contract_sha256"] != contract_sha256(contract):
        raise ValueError("Feedback contract differs from measured predicate")
    if data["status"] != "FAIL":
        raise ValueError("Only a measured failure supplies geometric negative feedback")
    return {"fixture": name, "label_kind": "GEOMETRIC_PREDICATE_FALSE",
            "predicate": "Declared bore region is empty", "binding_error_label": None,
            "semantic_training_eligible": False, "geometry_training_scope": "Original known-binding fixture only",
            "evidence": {"contract": contract, "report": data}}


def run(args):
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new or empty example output directory")
    output.mkdir(parents=True, exist_ok=True)
    def execute(argv, name):
        process = subprocess.run(argv, capture_output=True, timeout=600)
        (output / (name + ".log")).write_bytes(process.stdout + process.stderr)
        if process.returncode:
            raise RuntimeError(name + " failed; inspect its saved log")
    execute([str(args.cad_python), "-I", str(ROOT / "examples/semantic_binding/generate_demo.py"),
             "--output", str(output)], "generate")
    execute([str(args.geometry_python), str(ROOT / "tools/render_entity_views.py"), "--step", str(output / "assembly.step"),
             "--queries", str(output / "queries.json"), "--output", str(output / "views")], "render")
    mapping = fixture_mapping(json.loads((output / "views/entities.private.json").read_text(encoding="utf-8")))
    save(output / "fixture-mapping.json", mapping)
    execute([str(args.model_python), str(ROOT / "tools/encode_entity_views.py"), "encode", "--manifest",
             str(output / "views/views.private.json"), "--model-dir", str(args.model_dir.resolve()),
             "--output", str(output / "embeddings"), "--device", args.device, "--batch-size", "32"], "encode")
    queries = json.loads((output / "queries.json").read_text(encoding="utf-8"))
    rankings = []
    for index, query in enumerate(queries):
        report = bind_dimension(query["text"], output / "assembly.step", embedding_index=output / "embeddings/index.json",
                                query_embedding=output / ("embeddings/query-%04d.json" % index), top_k=3)
        save(output / ("ranking-%d.json" % index), report)
        (output / ("ranking-%d.html" % index)).write_text(_html(report), encoding="utf-8")
        rankings.append({"query_id": query["id"], "candidates": report["candidates"]})
    geometry, feedback = [], []
    contract = validate_contract(ROOT / "examples/semantic_binding/brief.yaml")
    for name in ("through", "blind", "solid"):
        report = diagnose(output / (name + ".step"), brief=contract,
                          reference=output / "through.step", cad_python=str(args.cad_python))
        report.to_json(output / (name + "-diagnosis.json"))
        report.to_html(output / (name + "-diagnosis.html"))
        data = report.to_dict()
        geometry.append({"fixture": name, "status": report.status,
                         "requirements": data["requirements"], "inputs": data["inputs"]})
        if report.status == "FAIL":
            feedback.append(feedback_record(name, data, contract))
    if [row["status"] for row in geometry] != ["PASS", "FAIL", "FAIL"]:
        raise ValueError("Analytic geometry controls failed; retain outputs for inspection")
    # A failed geometric predicate does not supply a document-to-entity label.
    save(output / "geometric-feedback.json", feedback)
    save(output / "acceptance.json", {"schema_version": "hardcad.semantic-demo.v1", "rankings": rankings,
         "geometry": geometry, "feedback_count": len(feedback), "binding_accuracy": None,
         "scope": "Original three-solid demonstration; learned ranking, explicit geometric checks and training-label eligibility are separate."})
    cards = []
    for i, row in enumerate(geometry):
        image = base64.b64encode((output / "views" / mapping[row["fixture"]] / "view-0.png").read_bytes()).decode()
        cards.append("<article><img alt='Rendered STEP solid' src='data:image/png;base64," + image + "'><h2>"
                     + escape(row["fixture"]) + "</h2><p>Declared Ø8 through-region: " + row["status"]
                     + "</p><a href='" + row["fixture"] + "-diagnosis.html'>Geometric report</a></article>")
    html = """<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Hard-CAD semantic binding example</title><style>body{font:16px system-ui;max-width:1080px;margin:40px auto;padding:0 20px;color:#243441}h1{font-weight:600}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}article{border:1px solid #ccd6db;border-radius:8px;padding:16px}img{width:100%;max-width:224px}a{color:#176a82}pre{white-space:pre-wrap}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style>
<h1>Find a candidate. Check the requirement.</h1><p>Real CLIP image–text ranking and exact FreeCAD volume checks on three original STEP fixtures.</p><div class='grid'>"""
    html += "".join(cards) + "</div><h2>Learned retrieval</h2><p><a href='ranking-0.html'>Through-hole query</a> · <a href='ranking-1.html'>Solid-plate query</a></p>"
    html += "<p>Cosine similarity ranks candidates; it is not calibrated confidence. The explicit bore contract provides the separate geometric test. A failed test does not automatically identify a binding error.</p>"
    (output / "index.html").write_text(html, encoding="utf-8")
    print(json.dumps({"geometry": [r["status"] for r in geometry], "ranking_queries": len(rankings), "feedback_records": len(feedback)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cad-python", type=Path, required=True)
    parser.add_argument("--geometry-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--model-python", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    run(parser.parse_args())
