# cad15: IoU improves while a side-cut regresses

## Open or remeasure the shipped bundle

Open [report.html](report.html) locally for the paired changes, or inspect the
[initial](initial.html) and [feedback](feedback.html) diagnoses. The three
[reference](reference.step), [initial](initial.step) and [feedback](feedback.step)
STEP files are curated, redistributable reconstructions. The
[provenance manifest](provenance.json) binds these bytes, the measurements and
the source recipes; they are not private industrial models or new generations.

After `python -m pip install '.[yaml]'`, run from this example directory:

```sh
hardcad-diagnose feedback.step --reference reference.step --brief brief.yaml --cad-python FREECAD_PYTHON --html rechecked.html --json rechecked.json
```

Use fresh output filenames. Exit 1 means at least one declared requirement
fails; this is a measured diagnosis, not an execution failure. The joint replay
below returns 0 when it reproduces all recorded values and expected failures.

To regenerate both distributable bundles from the repository root:

```sh
python -m tools.export_validator_examples --output exported-examples --cad-python FREECAD_PYTHON
```

## Replay from the packaged recipes

This example replays the recorded 7B initial/feedback pair. IoU increases and
extra material decreases by approximately 28.27 mm³, while the declared side-cut
region changes from clear to occupied by approximately 28.27 mm³.

Install the SDK with YAML support from the repository root, then run:

```sh
python -m pip install '.[yaml]'
python examples/cad15_iou_improves_cut_regresses/run.py --output cad15-demo --cad-python FREECAD_PYTHON
```

Use an output directory that does not exist. The shared installed replay first
reconstructs and verifies both cad15/cad30, then this script diagnoses cad15
through `diagnose(..., brief="brief.yaml")`. It checks that the YAML contract
and measurements equal the verified JSON path. Open
`cad15-demo/cad15/brief-feedback.html` and compare it with `brief-initial.html`.
`result.json` and `cad15/difference.json` retain the source bindings and deltas.

The explicit `brief.yaml` copies the declared regions from the packaged
[`cad15_cad30.json`](../../hardcad/examples/cad15_cad30.json) asset. That asset
records the original case, program and result hashes; the regression tests check
those files and compare the reconstructed geometry with the recorded programs.
The replay creates no new generation sample. Its success means numerical replay
agreement; the feedback candidate intentionally has a failed requirement.

See [API and contract details](../../docs/VALIDATOR_QUICKSTART.md) and
[source-bound replay details](../../docs/VALIDATOR_PAPER_EXAMPLES.md). These
controlled constructions and scripts use `LICENSE-CODE`; no private CAD corpus
or model service is required.
