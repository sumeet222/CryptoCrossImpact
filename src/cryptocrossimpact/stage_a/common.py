"""Isolated Stage A artifacts, preservation and exact scientific identities."""
import json
from pathlib import Path
import yaml
from ..data.storage import sha256,utcnow
from ..evaluation.v2_common import save,digest


def paths(root):
    root=Path(root);out=root/'reports/research/extension_a_artifacts';bulk=root/'results/extension_a'
    out.mkdir(parents=True,exist_ok=True);bulk.mkdir(parents=True,exist_ok=True)
    return out,bulk


def config(root):return yaml.safe_load((Path(root)/'configs/extension_a_liquidity_impact.yaml').read_text())


def binding(root):
    root=Path(root)
    files=list((root/'src/cryptocrossimpact').rglob('*.py'))+[root/'configs/extension_a_liquidity_impact.yaml',root/'docs/extensions/a_liquidity_impact_protocol_v1.md',root/'scripts/extension_a.py']
    return {str(p.relative_to(root)):sha256(p) for p in sorted(files) if '__pycache__' not in str(p) and p.name!='reporting.py'}


def preserve(root):
    root=Path(root);out,_=paths(root);r=json.loads((out/'preservation_initial.json').read_text())
    changed=[n for n,h in r['files'].items() if not (root/n).is_file() or sha256(root/n)!=h]
    changed += [n for n,v in r['data_stats'].items() if not (root/n).exists() or [(root/n).stat().st_size,(root/n).stat().st_mtime_ns]!=v]
    result=dict(status='PASS' if not changed else 'HOLD',files=len(r['files']),data_stat_snapshots=len(r['data_stats']),changed=changed,utc=utcnow())
    save(out/'preservation_final.json',result)
    if changed:raise ValueError('Prior artifact preservation HOLD: '+str(changed))
    return result
