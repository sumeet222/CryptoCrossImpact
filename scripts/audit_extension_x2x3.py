#!/usr/bin/env python3
"""Public audit entry point; require complete phase checkpoints first."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cryptocrossimpact.robust.audit import audit
p=argparse.ArgumentParser();p.add_argument('--holdout',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/'reports/research/extension_x2x3_artifacts'
if a.holdout:
    record=json.loads((out/'holdout_gate_audit.json').read_text())
    if record['status']!='COMPLETE':raise SystemExit('Audit HOLD: holdout phase incomplete')
else:
    for phase in ['selection','combined']:
        path=out/f'run_{phase}.json'
        if not path.exists():raise SystemExit('Audit HOLD: '+phase+' phase incomplete')
        record=json.loads(path.read_text())
        if record['complete']!=736 or record['failed']:raise SystemExit('Audit HOLD: '+phase+' phase incomplete')
print(audit(root,a.holdout))
