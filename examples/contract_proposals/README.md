# From model proposals to measured requirements

Run from the repository root with Python 3.10 or newer:

```sh
python examples/contract_proposals/replay.py
```

This offline example checks frozen protocol/result SHA-256 identities and their
public source bindings, reconstructs the controlled prompts and reference
enumeration, and recomputes published aggregates from individual records. It
does not call GLM, load a CAD kernel, or read private responses and STEP files.
An optional `--output NEW_FILE.json` writes the verification report without
overwriting an existing file. Exit 0 means `VERIFIED_PUBLIC_RECEIPTS`;
exit 2 means a failed check or output error.

The checked run contains 30 template descriptions with explicit part indices,
world coordinates and millimetres. The service reported
`GLM-5.3-Flash-EXL3`; the experiment did not independently identify its weights.
Its strict JSON interface accepted 22/30 responses and matched 41/61 authored
cut operations. Eight whole responses were rejected. Full-cohort precision
remains null because the rejected proposal counts are unknown; recall retains
all 61 reference operations.

A separately frozen, post-hoc decoder removes one complete outer JSON fence.
Reusing the same responses, with no new inference or field correction, matches
61/61 operations. This is an interface sensitivity result, not held-out evidence
that arbitrary prose can be bound automatically.

The downstream records retain 99 archived CAD endpoints. Strict parsing covers
119/169 applicable requirement instances, leaving 50 unavailable; decoded
proposals preserve 169/169 local verdicts. Six no-cut endpoints are not
applicable, and 16 Boolean-unavailable endpoints remain unavailable. These are
controlled recipe-bound measurements, not precision/recall on the 22 original
engineering documents or full U/action propagation.

## What the example verifies

The executable checks seven frozen protocol/result anchors, their recorded
implementation and upstream-file hashes, the ordered cohort, prompt hashes,
same-response decoding identities, item-level aggregates, and all downstream
allocation/coverage totals. It imports existing aggregation functions from
`tools/run_binding_proposal_pilot.py` and
`tools/measure_binding_propagation.py`.

Public receipt verification cannot independently remeasure private geometry or
inspect response bytes. The output states `private_artifacts_verified: false`,
`new_model_calls: 0`, and `new_geometry_measurements: 0`. A changed result or
protocol fails rather than silently updating this example's expected hashes.

## Re-running geometry with the original private inputs

Read [the experiment guide](../../docs/EXPERIMENT_GUIDE.md) first. Supply a
FreeCAD Python executable and the original hash-bound archived run/proposal
directories. In PowerShell, after setting `HARDCAD_CAD_PYTHON`,
`HARDCAD_ARCHIVED_RUN_ROOT`, and `HARDCAD_PROPOSALS` to those existing resources:

```powershell
python tools/measure_binding_propagation.py run --cad-python "$env:HARDCAD_CAD_PYTHON" --run-root "$env:HARDCAD_ARCHIVED_RUN_ROOT" --proposals "$env:HARDCAD_PROPOSALS" --output build/contract-proposals-strict-replay.json
python tools/measure_binding_propagation.py run --cad-python "$env:HARDCAD_CAD_PYTHON" --run-root "$env:HARDCAD_ARCHIVED_RUN_ROOT" --proposals "$env:HARDCAD_PROPOSALS" --decoding outer-fence --output build/contract-proposals-decoded-replay.json
```

The decoded path additionally requires the matching private decoded manifest
and receipts in the `decoded/` subdirectory of `HARDCAD_PROPOSALS` (originally
`build/revision-1019/binding-pilot/decoded/`). Neither command makes model calls.
Missing or changed source artifacts
cause failure; a public clone alone does not contain the original inputs.

## Re-running inference is a separate operation

The frozen inference runner is
[`tools/run_binding_proposal_pilot.py`](../../tools/run_binding_proposal_pilot.py).
Its `--work` directory must be new, under ignored `build/`, and its configured
local service must advertise the frozen model label. The command below makes
up to 30 model calls under the frozen budget. Use a separate experimental checkout:
the runner writes its canonical `results/binding_proposal_pilot.json`, which
will intentionally differ from this example's historical receipt anchor.

```powershell
python tools/run_binding_proposal_pilot.py run --cad-python "$env:HARDCAD_CAD_PYTHON" --work build/contract-proposals-new-inference
```

Do not replace the recorded experiment with that new run. Preserve its new
timestamps, responses and result identity. Service setup and the distinction
between the pilot's recipe-indexed primitives and executable SDK contracts are
described in [model proposals](../../docs/VALIDATOR_MODEL_PROPOSALS.md).
