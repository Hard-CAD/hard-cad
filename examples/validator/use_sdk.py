"""Run the installed SDK on generated demo files; no repository tools imported."""
import argparse
import json
from pathlib import Path

from hardcad import diagnose, compare


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models', required=True)
    p.add_argument('--contract', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--cad-python', required=True)
    args = p.parse_args()
    models, out = Path(args.models), Path(args.output)
    if out.exists() and any(out.iterdir()):
        p.error('use an empty output directory')
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    for stage in ('before', 'after'):
        report = diagnose(models/(stage+'.step'), args.contract,
                          reference=models/'reference.step', cad_python=args.cad_python)
        report.to_json(out/(stage+'.json'))
        report.to_html(out/(stage+'.html'))
        reports.append(report)
    difference = compare(*reports)
    (out/'difference.json').write_text(json.dumps(difference, indent=2)+'\n', encoding='utf-8')
    print('Wrote two source-bound JSON/HTML reports and a compatible revision difference.')


if __name__ == '__main__':
    main()
