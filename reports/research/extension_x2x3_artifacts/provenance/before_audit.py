"""Independent prefix/constraint/source and complete cash-cost output checks."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ..data.storage import sha256,utcnow
from ..execution.impact_cost import triangular_cash
from .common import paths,save,preserve,binding
from .protocol import verify_decisions
from .workflow import model_bundle,development_episodes


def audit(root,holdout=False):
    root=Path(root);out,bulk=paths(root);folders=[bulk/'holdout'] if holdout else [bulk/'selection',bulk/'combined']
    episodes={e.episode_id:e for e in development_episodes(root)} if not holdout else {}
    numbers=set();prefixes=0;cash_error=0.;triangular_checks=0;parity=0.;last=None
    for folder in folders:
        for path in sorted(folder.glob('*.json')):
            if path.name.endswith('_decisions.json') or '_prefix_' in path.name:continue
            r=json.loads(path.read_text());eid=r['episode_id'];numbers.add(eid);dpath=root/r['decision_path'];d=verify_decisions(root,dpath)
            if sha256(dpath)!=r['decision_sha256']:raise ValueError('Decision receipt changed')
            if digest_code(r['signature']) is False:raise ValueError('Malformed signature')
            if len(eid)!=14:raise ValueError('Unknown episode identity')
            origin=pd.Timestamp(eid[:8]+'T'+eid[9:13]+'00Z');month=origin.strftime('%Y-%m')
            if month!=last:b,ws=model_bundle(root,month,origin);last=month
            ws={w.world_id:w for w in ws}
            if d['world_hashes']!={n:w.world_hash for n,w in ws.items()}:raise ValueError('Common evaluator changed')
            with np.load(folder/r['schedule_file']) as data:
                x=np.array(d['initial']);beta=d['beta'];sigma=np.array(d['covariance'])
                for policy,records in r['records'].items():
                    z=data[policy];cap_hash=d['caps_hash']
                    if np.max(np.abs(z.sum(axis=0)-x)/x)>1e-7 or (z < -1e-7*x).any():raise ValueError('Terminal/sell failure')
                    committed=[]
                    for record,proof in zip(records,d['prefixes']):
                        p=json.loads((root/proof['path']).read_text());cut=record['k'];clock=origin+pd.Timedelta(minutes=cut)
                        if pd.Timestamp(record['asof'])!=clock or pd.Timestamp(record['latest_open'])!=clock-pd.Timedelta(minutes=1):raise ValueError('Clock/causality failure')
                        np.testing.assert_array_equal(np.array(p['committed'][policy]),np.array(record['prefix']))
                        if record['primal']>1e-7 or record['kkt']>2e-5 or record.get('epigraph_gap',0)>2e-5:raise ValueError('KKT/primal/epigraph failure')
                        committed.extend(record['prefix']);prefixes+=1
                    np.testing.assert_array_equal(z,np.array(committed))
                for qa in r['diagnostics']:
                    if qa['caps_hash']!=d['caps_hash'] or qa['covariance_hash']!=__import__('cryptocrossimpact.evaluation.v2_common',fromlist=['digest']).digest(sigma) or qa['beta']!=beta or qa['cap_violations'] or qa['repairs']:raise ValueError('Matched constraint/risk failure')
                # Six predeclared first-of-month arrival audits; full schedule
                # triangular sums independent of original H quadratic scorer.
                if origin.day==1 and origin.hour==0:
                    for row in r['scores']:
                        if row['world'] not in ['E1','E2']:continue
                        cash=triangular_cash(ws[row['world']].kernel,data[row['policy']]);error=abs(cash-row['transient_usdt']);cash_error=max(cash_error,error);triangular_checks+=1
                        if error>1e-8*max(abs(cash),1):raise ValueError('Independent cash check failed')
                for error in r['parity'].values():parity=max(parity,error)
    expected=368 if holdout else 736
    if len(numbers)!=expected:raise ValueError('Incomplete common universe')
    result=dict(status='PASS',utc=utcnow(),episodes=len(numbers),prefixes=prefixes,independent_triangular_checks=triangular_checks,
        maximum_cash_error_usdt=cash_error,maximum_X1_nominal_schedule_error_over_initial=parity,
        preservation=preserve(root,True),code=binding(root))
    save(out/('holdout_output_audit.json' if holdout else 'development_output_audit.json'),result);return result


def digest_code(s):return isinstance(s,str) and len(s)==64
