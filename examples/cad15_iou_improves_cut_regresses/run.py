"""Replay the recorded pair and exercise the explicit YAML brief API."""
import argparse
import json
from pathlib import Path

from hardcad import compare, diagnose
from hardcad.contracts import validate_contract
from hardcad.demo import run_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    parser.add_argument('--cad-python', help='FreeCAD Python executable; or set HARDCAD_CAD_PYTHON')
    args = parser.parse_args()
    receipt = run_demo(args.output, cad_python=args.cad_python)
    if receipt['status'] != 'PASS':
        raise SystemExit('Recorded-pair replay failed; inspect result.json')
    case_dir = args.output / 'cad15'
    brief = Path(__file__).with_name('brief.yaml')
    if validate_contract(brief) != validate_contract(case_dir / 'contract.json'):
        raise SystemExit('Example brief differs from the source-bound replay contract')
    reports = {}
    for stage in ('initial', 'feedback'):
        report = diagnose(candidate=case_dir / (stage + '.step'),
                          reference=case_dir / 'reference.step', brief=brief,
                          cad_python=args.cad_python)
        recorded = json.loads((case_dir / (stage + '.json')).read_text(encoding='utf-8'))
        if report.to_dict() != recorded:
            raise SystemExit('YAML diagnosis differs from the verified JSON diagnosis')
        report.to_json(case_dir / ('brief-' + stage + '.json'))
        report.to_html(case_dir / ('brief-' + stage + '.html'))
        reports[stage] = report
    changes = compare(reports['initial'], reports['feedback'])
    print(json.dumps({'case_id': 'cad15', 'replay_status': receipt['status'],
                      'global_metric_deltas': changes['global_metric_deltas'],
                      'transition_counts': changes['transition_counts']}, indent=2))


if __name__ == '__main__':
    main()
