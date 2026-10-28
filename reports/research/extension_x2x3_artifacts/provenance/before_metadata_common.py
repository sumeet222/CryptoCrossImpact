"""X2+X3 identities, preservation and compact serialization."""
import json
from pathlib import Path
import subprocess
import yaml
from ..data.storage import sha256,utcnow
from ..evaluation.v2_common import save,digest

START='2026-07-01T00:00:00Z'
END='2026-10-01T00:00:00Z'


def paths(root):
    root=Path(root);out=root/'reports/research/extension_x2x3_artifacts';bulk=root/'results/extension_x2x3'
    out.mkdir(parents=True,exist_ok=True);bulk.mkdir(parents=True,exist_ok=True)
    return out,bulk


def config(root):return yaml.safe_load((Path(root)/'configs/extension_x2x3.yaml').read_text())


def preserve(root,verify=False):
    root=Path(root);out,_=paths(root);path=out/'preservation_initial.json'
    if path.exists():
        initial=json.loads(path.read_text())
        if not verify:return initial
        changed=[n for n,h in initial['files'].items() if not (root/n).exists() or sha256(root/n)!=h]
        changed += [n for n,v in initial['data_stats'].items() if not (root/n).exists() or [(root/n).stat().st_size,(root/n).stat().st_mtime_ns]!=v]
        result=dict(files=len(initial['files']),data_files=len(initial['data_stats']),changed=changed)
        save(out/'preservation_final.json',result)
        if changed:raise ValueError('Preservation HOLD: '+str(changed))
        return result
    files={};stats={}
    for folder in ['src','scripts','tests','configs','docs','reports','figures','results','references','prompts','data/registry']:
        for p in (root/folder).rglob('*'):
            if not p.is_file() or '__pycache__' in str(p) or '/robust/' in str(p) or 'x2x3' in str(p).lower():continue
            files[str(p.relative_to(root))]=sha256(p)
    for name in ['AGENTS.md','README.md','SPEC_CHANGELOG.md','requirements.txt','CryptoCrossImpact_Research_Specification_v1_2026-10-27.md']:
        files[name]=sha256(root/name)
    for base in ['data/raw','data/canonical']:
        for p in (root/base).rglob('*'):
            if p.is_file():stats[str(p.relative_to(root))]=[p.stat().st_size,p.stat().st_mtime_ns]
    initial=dict(utc=utcnow(),files=files,data_stats=stats,branch=subprocess.check_output(['git','branch','--show-current'],text=True,cwd=root).strip(),
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip(),dirty=subprocess.check_output(['git','status','--short'],text=True,cwd=root))
    save(path,initial);return initial


def sources(root):
    root=Path(root)
    return sorted(p for p in (root/'src/cryptocrossimpact').rglob('*.py') if '__pycache__' not in str(p) and p.name!='reporting.py')+[
        root/'scripts/extension_x2x3.py',root/'configs/extension_x2x3.yaml',root/'docs/extensions/x2x3_robust_liquidity_protocol_v1.md']


def binding(root):return {str(p.relative_to(root)):sha256(p) for p in sources(root)}


def eligibility(root):
    root=Path(root);out,_=paths(root)
    if (out/'holdout_eligibility.json').exists():return json.loads((out/'holdout_eligibility.json').read_text())
    # Positive recorded execution/source scopes; no candidate holdout values read.
    original=json.loads((root/'data/registry/source_manifest.json').read_text())
    x1=json.loads((root/'reports/research/extension_x1_artifacts/run_manifest.json').read_text())
    stage5=json.loads((root/'reports/research/stage05_v2_artifacts/verdict_v2.json').read_text())
    months=sorted({k.split('/')[-1] for k in original['partitions']})
    scopes=[]
    for p in (root/'reports/sessions').glob('*.md'):
        text=p.read_text()
        scopes.append(dict(path=str(p.relative_to(root)),sha256=sha256(p),scope_assertions=[s for s in text.splitlines() if any(w in s.lower() for w in ['july','september','2026-06','2026 canonical','no2026','2026 final','no fresh','jan–jun'])]))
    # Unknown new data/performance namespaces are not automatically declared unseen.
    suspicious=[str(p.relative_to(root)) for base in ['results','reports','data/canonical','data/raw'] for p in (root/base).rglob('*')
        if p.is_file() and any(s in p.name for s in ['2026-07','2026-08','2026-09','202607','202608','202609']) and 'extension_x2x3' not in str(p)]
    eligible=max(months)=='2026-06' and x1['future_test_partitions_opened']==0 and not suspicious
    value=dict(status='ELIGIBLE' if eligible else 'UNKNOWN',utc=utcnow(),dates=[START,END],
        basis='Affirmative original acquisition scope through June2026, complete prior-run/session lineage, Stage5 locked Jan–Jun outcomes and X1 strict development-only read evidence; not file absence alone.',
        source_months=months,X1_data_period=x1['data_period'],X1_manifest_sha256=sha256(root/'reports/research/extension_x1_artifacts/run_manifest.json'),
        stage5_verdict_sha256=sha256(root/'reports/research/stage05_v2_artifacts/verdict_v2.json'),prior_session_scopes=scopes,
        suspicious_candidate_paths=suspicious,new_holdout_values_opened=False,limitation='Covers recorded work in this project, not unrecorded activity elsewhere.')
    save(out/'holdout_eligibility.json',value);return value
