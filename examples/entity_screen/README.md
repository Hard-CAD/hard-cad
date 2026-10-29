# Source-bound entity screening

Run from the repository root with Python 3.10 or newer:

```sh
python examples/entity_screen/replay.py
```

This offline example verifies frozen public protocol/result hashes, their
upstream bindings and ordered document cohort. It calls the existing
`tools/audit_document_entity_candidates.py:summarize` function on recorded rows
and checks equality with the published summary. It needs no OCP, original DOCX,
STEP input, model weights, or network service. An optional
`--output NEW_FILE.json` saves its report without replacing existing files.

The recorded inventory contains 22 imported cases and 2,086 solid occurrences.
Thirteen documents supply an explicit-unit dimension tuple for screening;
their associated STEP files contain 1,576 occurrences. Eight other documents
retain unresolved units, and one has no target tuple. These are tuple fields,
not 39 independent dimension samples.

Across the 13 screened tuples, no solid matches at the numerical 0.0001 mm
band or at 1% and 5%, even allowing the six declared axis permutations. At 10%,
one tuple has one candidate under an axis permutation; the other 12 have none.
The fixed XYZ mapping has no candidates at any reported band. Those descriptive
bands are not manufacturing tolerances. A unique coarse candidate is not a
verified entity/frame binding.

The summary also preserves zero source-paragraph product-name matches and zero
explicit XYZ assignment markers. Literal-name screening makes no translation
or fuzzy-match inference. This is an auditable candidate screen, not semantic
precision/recall or a judgment that the original document is unusable.

## What is and is not replayed

`VERIFIED_PUBLIC_RECEIPTS` means public file identities and summary arithmetic
matched. It does not mean the example re-imported geometry or verified private
source bytes. Its JSON explicitly reports `private_artifacts_verified: false`,
`new_geometry_measurements: 0`, and `new_model_calls: 0`.

The protocol preserves source hashes so an authorized holder can remeasure
the same inputs. Read [the experiment guide](../../docs/EXPERIMENT_GUIDE.md)
before preparing that environment. With OCP **7.9.3.1** installed in the chosen
interpreter, set `HARDCAD_DOCX_MANIFEST` and `HARDCAD_CORPUS_ROOT` to the existing
hash-bound private manifest and source tree, then run from the repository root:

```powershell
python tools/audit_document_entity_candidates.py run --manifest "$env:HARDCAD_DOCX_MANIFEST" --corpus-root "$env:HARDCAD_CORPUS_ROOT" --output build/entity-screen-replay.json --private-output build/entity-screen-replay/receipt.private.json
```

The original manifest, source files, and frozen public upstream receipts are
required; the command rejects changed inputs and other OCP versions. Exact dimensions,
names and occurrence indices stay in the ignored private output. A public
clone cannot recreate those private measurements from summary hashes alone.

The separate [embedding proposal interface](../../docs/VALIDATOR_BINDING.md)
can rank learned semantic candidates. It does not reinterpret this numerical
screen as a learned model or convert candidate similarity into certification.
