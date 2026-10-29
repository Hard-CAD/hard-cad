# Learned candidates and exact bore checks

This source-checkout example builds three original STEP solids: a through-hole
plate, a blind-hole plate and a solid plate. It renders each solid, computes
real pretrained CLIP embeddings, ranks two text queries with `bind_dimension`,
then independently checks an explicit Ø8 through-region with FreeCAD.

Install the SDK with YAML support. Rendering needs OCP, NumPy and Pillow;
the separate model interpreter needs PyTorch, Transformers and safetensors.
FreeCAD runs in its own configured interpreter.

```sh
python -m pip install '.[yaml]'
MODEL_PYTHON tools/encode_entity_views.py prepare-model --model-dir MODEL_DIRECTORY
python examples/semantic_binding/run.py --output semantic-demo --cad-python FREECAD_PYTHON --geometry-python OCP_PYTHON --model-python MODEL_PYTHON --model-dir MODEL_DIRECTORY --device cuda
```

Use `--device cpu` without a compatible GPU. Model preparation downloads only
the pinned official CLIP ViT-B/32 files and verifies their identities; inference
uses local files. Open `semantic-demo/index.html` for images, rankings and exact
geometry reports. Every output directory must be new or empty.

The expected geometric controls are PASS / FAIL / FAIL. Learned rank positions
are measured outputs, not hard-coded acceptance conditions. The model is a
multiview image–text baseline, not BRepCLIP or BrepLLM. Centering and scaling the
views removes absolute dimensions, so similarity does not establish an 8 mm
diameter, a through passage or a document-to-entity correspondence.

`geometric-feedback.json` records failed predicates with source hashes. These
can be negative examples for the **declared geometric predicate on this known
fixture**. They have `binding_error_label: null` and are ineligible for semantic
binding training: a blocked bore alone cannot tell whether the document was
misread, the entity was misbound, or the candidate geometry is defective.

Model weights, original industrial models and corpus embeddings are not bundled
with this example. The fixture construction and this example code are original
Hard-CAD code under `LICENSE-CODE`.
