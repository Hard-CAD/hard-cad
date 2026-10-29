"""Generate original through-hole, blind-hole and solid-plate STEP fixtures."""
import argparse
import json
from pathlib import Path


def generate(output):
    import FreeCAD as App
    import Part
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plate = Part.makeBox(36, 24, 6)
    bore = Part.makeCylinder(4, 6, App.Vector(18, 12, 0))
    through = plate.cut(bore)
    blind = plate.cut(Part.makeCylinder(4, 4, App.Vector(18, 12, 2)))
    for name, shape in (("through", through), ("blind", blind), ("solid", plate)):
        if not shape.isValid():
            raise ValueError("invalid generated fixture")
        shape.exportStep(str(output / (name + ".step")))
    blind_view = blind.copy(); blind_view.translate(App.Vector(50, 0, 0))
    solid_view = plate.copy(); solid_view.translate(App.Vector(100, 0, 0))
    Part.makeCompound([through, blind_view, solid_view]).exportStep(str(output / "assembly.step"))
    (output / "queries.json").write_text(json.dumps([
        {"id": "through-hole", "text": "A metal plate with a circular through hole."},
        {"id": "solid-plate", "text": "A solid rectangular metal plate without holes."},
    ], indent=2) + "\n", encoding="utf-8")
    (output / "fixture.json").write_text(json.dumps({
        "source": "original deterministic fixture", "unit": "mm", "frame": "world",
        "plate_dimensions": [36, 24, 6], "bore_diameter": 8,
        "through_depth": 6, "blind_depth": 4,
        "note": "Analytic construction; no industrial semantic labels or measured learned-binding accuracy."
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    generate(parser.parse_args().output)
