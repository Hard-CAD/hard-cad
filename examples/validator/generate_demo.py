"""Create original, rights-clear demo solids using the FreeCAD interpreter.

Both candidates have the same overlap/extra/missing volumes but violate different
declared channels. This analytic demonstration is not generated-model evidence.
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    names = ('reference.step', 'before.step', 'after.step', 'expected.json')
    if any((out/n).exists() for n in names):
        parser.error('refusing to overwrite demo files; use a new output directory')
    import FreeCAD as App
    import Part
    out.mkdir(parents=True, exist_ok=True)
    plate = Part.makeBox(10, 10, 10)
    a = Part.makeBox(2, 2, 10, App.Vector(2, 2, 0))
    b = Part.makeBox(2, 2, 10, App.Vector(6, 6, 0))
    shapes = {'reference': plate.cut(a).cut(b), 'before': plate.cut(b), 'after': plate.cut(a)}
    for name, shape in shapes.items():
        if not shape.isValid():
            raise ValueError('invalid demo construction')
        shape.check(True)
        shape.exportStep(str(out/(name+'.step')))
    expected = {
        'basis': 'Analytic declared construction, not empirical model performance.',
        'volume_unit': 'mm3', 'reference_volume': 920, 'candidate_volume': 960,
        'before_and_after_iou': 920/960, 'before_and_after_extra': 40,
        'before_and_after_missing': 0,
        'before_statuses': {'channel-A': 'FAIL', 'channel-B': 'PASS', 'support-wall': 'PASS'},
        'after_statuses': {'channel-A': 'PASS', 'channel-B': 'FAIL', 'support-wall': 'PASS'},
    }
    (out/'expected.json').write_text(json.dumps(expected, indent=2)+'\n', encoding='utf-8')
    print('Created three declared demonstration solids and analytic expectations.')


if __name__ == '__main__':
    main()
