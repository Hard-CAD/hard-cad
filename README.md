# Hard-CAD: Contract-Based Diagnostics for Generated CAD Geometry

<div align="center">

[![Paper](https://img.shields.io/badge/Paper-Computers%20%26%20Graphics-blue.svg)](assets/Hard-CAD.pdf)
[![Project Page](https://img.shields.io/badge/Homepage-Project%20Page-emerald.svg)](index.html)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

**"Don't just measure IoU. Diagnose the requirement."**

</div>

---

Hard-CAD checks declared geometric requirements and compares their states across CAD revisions. It bridges human design briefs to deterministic OpenCASCADE B-Rep kernel measurements, diagnosing localized defects that standard global metrics (such as IoU or Chamfer Distance) obscure.

<div align="center">
  <img src="assets/diagnostic_concept.png" width="90%" alt="Hard-CAD Diagnostic Concept" />
</div>

## 🔍 Why IoU Fails: The Dilemma

In CAD generation and iterative model repair:
- A revision can **improve global IoU** (e.g. `+0.000126`) and reduce unwanted extra volume (`-28.27 mm³`), while **catastrophically regressing a declared functional cut** from `PASS (0.00 mm³)` to `FAIL (28.27 mm³)` (observed in `cad15`).
- Conversely, a revision can successfully clear a blocked functional void while massively growing extra material along unrelated boundaries (observed in `cad30`).

Hard-CAD solves this by formalizing explicit schema contracts (keep-out voids, bounds, frames, units, and `1.0e-6 mm³` tolerances) and producing paired revision diffs.

<div align="center">
  <img src="assets/contract_revision_workflow.png" width="95%" alt="Workflow" />
</div>

---

## ⚡ Quickstart

### 1. Installation
```bash
git clone https://github.com/Hard-CAD/hard-cad.git
cd hard-cad
pip install .[yaml]
```

### 2. Run Verifiable Paper Demo
```bash
hardcad demo --output paper-demo --cad-python python
```
Open `paper-demo/index.html` to inspect the generated interactive reports.

### 3. Python API
```python
from hardcad import diagnose

report = diagnose(
    candidate="model.step",
    reference="reference.step",
    brief="brief.yaml",
    cad_python="python"
)
report.to_html("diagnosis.html")
print(report.summary())
```

---

## 📂 Repository Contents

- `index.html`: Interactive academic project homepage.
- `assets/`: Paper manuscript PDF (`Hard-CAD.pdf`) and figures.
- `examples/`:
  - `cad15_iou_improves_cut_regresses/`: Case study 1 reproducing cut regression under IoU gain.
  - `cad30_void_clears_extra_grows/`: Case study 2 reproducing void clearance under material growth.
  - `contract_proposals/`: Proposal-to-checker integration protocols.

---

## 📖 Citation

```bibtex
@article{hardcad2026,
  title   = {Hard-CAD: Contract-Based Diagnostics for Generated CAD Geometry},
  journal = {Computers \& Graphics},
  year    = {2026},
  note    = {Under Review}
}
```
