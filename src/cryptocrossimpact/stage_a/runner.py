"""Ordered Stage A execution with no automatic October outcome access."""
import json,subprocess,time,resource
from pathlib import Path
import pandas as pd
from ..data.storage import sha256,utcnow
from .common import paths,save,preserve,binding,digest


def tests(root,label='math',full=False):
    root=Path(root);out,_=paths(root);names=['tests/test_extension_a.py']
    if full:names+=['tests/test_extension_x1.py','tests/test_extension_x2x3.py','tests/test_stage01.py','tests/test_stage02_kernel.py','tests/test_stage03_execution.py','tests/test_stage04_policies.py','tests/test_stage05_evaluation.py','tests/test_stage05_v2.py']
    cmd=[str(root/'.venv/bin/python'),'-m','pytest',*names,'-m','not integration','-q','--junitxml='+str(out/f'{label}_pytest.xml')];r=subprocess.run(cmd,cwd=root,capture_output=True,text=True);(out/f'{label}_stdout.txt').write_text(r.stdout+r.stderr)
    save(out/f'{label}_tests.json',dict(returncode=r.returncode,command=cmd,utc=utcnow(),code=binding(root),junit_sha256=sha256(out/f'{label}_pytest.xml')))
    if r.returncode:raise ValueError('Stage A tests failed: '+str(out/f'{label}_stdout.txt'))
    print(r.stdout,flush=True)


def development(root,pilot=False):
    from .execution import fitted_models,replay
    from ..robust.workflow import development_episodes
    root=Path(root);out,bulk=paths(root);selected=json.loads((out/'eta_selection.json').read_text())['selected_eta'];results=[];start=time.perf_counter();last=None
    folder=bulk/(('pilot_'+digest(binding(root))[:10]) if pilot else 'development');folder.mkdir(exist_ok=True)
    for i,e in enumerate(development_episodes(root,pilot)):
        month=e.t0.strftime('%Y-%m')
        if month!=last:
            models={eta:fitted_models(root,month,eta) for eta in [.5,1]};last=month
        r=replay(root,e,models,selected,folder);results.append(r)
        if (i+1)%10==0:print('StageA development',i+1,'/736',round((time.perf_counter()-start)/60,2),'min',flush=True)
    label='pilot' if pilot else 'development'
    for key in ['scores','overload','diagnostics']:pd.DataFrame([a for r in results for a in r[key]]).to_csv(out/f'{label}_{key}.csv',index=False)
    save(out/f'{label}_run.json',dict(status='PASS',episodes=len(results),seconds=time.perf_counter()-start,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,code=binding(root),selected_eta=selected,maximum_triangle_error_usdt=max(r['triangle_error_usdt'] for r in results),new_October_values_opened=False))
    return results


def run(root,command):
    root=Path(root);out,bulk=paths(root)
    if command=='math':
        tests(root)
        from .execution import parity
        print(parity(root));preserve(root)
    elif command=='features':
        if json.loads((out/'math_tests.json').read_text())['returncode'] or json.loads((out/'baseline_parity.json').read_text())['status']!='PASS':raise ValueError('Math/real baseline gate required')
        from .fit import prepare
        prepare(root)
    elif command=='fit':
        from .calibration import calibrate,tail_check
        print(calibrate(root));tail_check(root)
    elif command in ['pilot','development']:development(root,command=='pilot')
    elif command=='report':
        from .reporting import report
        report(root)
    elif command=='confirmation':
        if not (out/'development_run.json').exists():raise ValueError('Complete development first')
        save(out/'confirmation_status.json',dict(status='CONFIRMATION_HOLD',reason='Optional October branch not opened: independent noninspection/official daily availability and a complete separately bound PRETEST_READY_A were not established. Core development completion does not force this optional experiment.',new_October_values_opened=False,ready_flag_created=False,utc=utcnow()))
    else:
        for part in ['math','features','fit','pilot','development']:run(root,part)
        tests(root,'final',True);run(root,'confirmation');run(root,'report');preserve(root)
