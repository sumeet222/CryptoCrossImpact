#!/usr/bin/env python3
"""X2+X3 ordered gates, development and independent holdout."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cryptocrossimpact.robust.common import preserve,eligibility


def main():
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser()
    p.add_argument('command',choices=['preflight','synthetic','pilot','selection','combined','development','freeze','holdout','report','all'])
    args=p.parse_args();cmd=args.command
    if cmd=='preflight':print(eligibility(root));print(preserve(root,True))
    elif cmd=='synthetic':
        import subprocess
        out=root/'reports/research/extension_x2x3_artifacts'
        code=subprocess.call([str(root/'.venv/bin/python'),'-m','pytest','tests/test_extension_x2x3.py','-q','--junitxml='+str(out/'synthetic_pytest.xml')],cwd=root)
        if code:raise SystemExit(code)
    elif cmd in ['pilot','selection','combined']:
        from cryptocrossimpact.robust.workflow import run,selection
        run(root,'selection' if cmd=='pilot' else cmd,cmd=='pilot')
        if cmd=='selection':print(selection(root))
        if cmd=='combined':
            from cryptocrossimpact.robust.audit import audit
            from cryptocrossimpact.robust.inference import summarize
            audit(root);print(summarize(root))
    elif cmd=='development':
        from cryptocrossimpact.robust.workflow import run,selection
        run(root,'selection');selection(root);run(root,'combined')
        from cryptocrossimpact.robust.audit import audit
        from cryptocrossimpact.robust.inference import summarize
        audit(root);print(summarize(root))
    elif cmd=='freeze':
        from cryptocrossimpact.robust.protocol import freeze
        print(freeze(root))
    elif cmd=='holdout':
        from cryptocrossimpact.robust.holdout import holdout
        holdout(root)
        from cryptocrossimpact.robust.audit import audit
        from cryptocrossimpact.robust.inference import summarize
        audit(root,True);print(summarize(root,True))
    elif cmd=='report':
        from cryptocrossimpact.robust.reporting import report
        report(root)
    else:
        from cryptocrossimpact.robust.workflow import run,selection
        from cryptocrossimpact.robust.protocol import freeze,run_tests,PretestHold
        from cryptocrossimpact.robust.holdout import holdout
        from cryptocrossimpact.robust.reporting import report
        from cryptocrossimpact.robust.audit import audit
        from cryptocrossimpact.robust.inference import summarize
        if not (root/'reports/research/extension_x2x3_artifacts/PRETEST_READY_X2X3.json').exists():
            eligibility(root);run_tests(root);run(root,'selection',True);run(root,'selection');selection(root);run(root,'combined');audit(root);summarize(root)
        freeze(root)
        try:holdout(root);audit(root,True);summarize(root,True)
        except PretestHold:report(root);raise
        report(root)
if __name__=='__main__':main()
