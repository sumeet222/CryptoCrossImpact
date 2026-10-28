"""Evidence-validated readiness: no caller supplied ready flag grants data access."""
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from ..data.storage import sha256,utcnow
from .common import paths,binding,config,save,digest,preserve,eligibility


class PretestHold(ValueError):pass

_READY_CACHE={}


def compatible_code(root,before):
    """Only archived audit/resume/Finder-metadata corrections are compatible.

    Scientific decision, forecast, fitting and scoring bytes are unchanged.
    Each accepted historical version has its actual source bytes retained.
    """
    root=Path(root);current=binding(root)
    if before==current:return True
    out,_=paths(root);path=out/'reviewed_audit_fix.json'
    if not path.exists():return False
    record=json.loads(path.read_text())
    if record['current_bindings']!=current or set(before)!=set(current):return False
    versions=[record['prior_bindings']]+record.get('intermediate_bindings',[])
    allowed={'src/cryptocrossimpact/robust/'+n for n in ['audit.py','protocol.py','workflow.py','common.py']}
    for n,h in current.items():
        if n not in allowed and before[n]!=h:return False
        if n in allowed:
            hashes={v[n] for v in versions}|{h}
            if before[n] not in hashes:return False
            for old in hashes-{h}:
                if not any(sha256(root/a)==old for a in record['version_archives'].get(n,[])):return False
    return True


def compatible_signatures(root,settings,specs):
    """Recognize archived execution identities without rewriting receipts."""
    import itertools
    root=Path(root);current=binding(root);out,_=paths(root);path=out/'reviewed_audit_fix.json'
    values={digest(dict(code=current,config=settings,specs=specs))}
    if not path.exists():return values
    record=json.loads(path.read_text());prior=record['prior_bindings']
    if not compatible_code(root,prior):return values
    versions=[prior]+record.get('intermediate_bindings',[])
    changed=[n for n in current if any(current[n]!=v[n] for v in versions)]
    choices=[sorted({current[n]}|{v[n] for v in versions}) for n in changed]
    for hashes in itertools.product(*choices):
        candidate=current.copy();candidate.update(zip(changed,hashes))
        values.add(digest(dict(code=candidate,config=settings,specs=specs)))
    return values


def require_closed_history(root,end):
    import pandas as pd
    root=Path(root);out,_=paths(root);start=pd.Timestamp('2026-07-01',tz='UTC');end=pd.Timestamp(end)
    if end<=start:return
    for month in pd.period_range(start.tz_localize(None),(end-pd.Timedelta(minutes=1)).tz_localize(None),freq='M'):
        path=out/f'closed_{month}.json'
        r=json.loads(path.read_text())
        if r['status']!='CLOSED' or r['complete']!=month.days_in_month*4:raise PretestHold('Prior holdout history not closed')


def verify_decisions(root,path):
    root=Path(root);path=Path(path);r=json.loads(path.read_text())
    if not r.get('prefixes') or len(r['prefixes'])!=12:raise PretestHold('Incomplete prefix commitments')
    if sha256(root/r['schedule_file'])!=r['schedule_sha256']:raise PretestHold('Schedule commitment changed')
    for row in r['prefixes']:
        if sha256(root/row['path'])!=row['sha256']:raise PretestHold('Prefix commitment changed')
    return r


def check_development(root):
    root=Path(root);out,_=paths(root)
    selection=json.loads((out/'development_selection.json').read_text())
    for name,h in selection['bindings'].items():
        if sha256(root/name)!=h:raise PretestHold('Selection inputs changed')
    for phase in ['selection','combined']:
        run=json.loads((out/f'run_{phase}.json').read_text())
        if run['complete']!=736 or run['failed'] or not compatible_code(root,run['code']):raise PretestHold('Development incomplete or numerical code changed')
    pilot=json.loads((out/'pilot_parity.json').read_text())
    if pilot['episodes']!=3 or pilot['nominal_max_error_over_initial']>1e-7:raise PretestHold('X1 parity incomplete')
    audit=json.loads((out/'development_output_audit.json').read_text())
    if audit['status']!='PASS' or audit['episodes']!=736:raise PretestHold('Development output audit incomplete')
    return selection


def run_tests(root):
    root=Path(root);out,_=paths(root);xml=out/'pretest_pytest.xml'
    command=[str(root/'.venv/bin/python'),'-m','pytest','tests/test_extension_x2x3.py','tests/test_extension_x1.py',
        'tests/test_stage01.py','tests/test_stage02_kernel.py','tests/test_stage03_execution.py','tests/test_stage04_policies.py',
        'tests/test_stage05_evaluation.py','tests/test_stage05_v2.py','-m','not integration','-q','--junitxml='+str(xml)]
    run=subprocess.run(command,cwd=root,text=True,capture_output=True)
    (out/'pretest_stdout.txt').write_text(run.stdout+run.stderr)
    suites=list(ET.parse(xml).getroot().iter('testsuite')) if xml.exists() else []
    failures=sum(int(x.attrib.get('failures',0))+int(x.attrib.get('errors',0)) for x in suites)
    count=sum(int(x.attrib.get('tests',0)) for x in suites)
    names=[x.attrib['name'] for x in ET.parse(xml).getroot().iter('testcase')] if suites else []
    result=dict(command=command,returncode=run.returncode,passed=count-failures,failures=failures,
        junit_sha256=sha256(xml) if xml.exists() else None,test_names=names,code=binding(root),
        tests_sha256={str(p.relative_to(root)):sha256(p) for p in (root/'tests').glob('test_*.py')},utc=utcnow(),integration_excluded=True)
    save(out/'pretest_tests.json',result)
    if run.returncode or failures or count<230:raise PretestHold('Required test suite failed/incomplete')
    return result


def freeze(root):
    root=Path(root);out,_=paths(root)
    if (out/'PRETEST_READY_X2X3.json').exists():return validate_ready(root)
    if (out/'first_source_value_open.json').exists():raise PretestHold('Cannot refreeze after holdout source access')
    selection=check_development(root);e=json.loads((out/'holdout_eligibility.json').read_text())
    if e['status']!='ELIGIBLE':raise PretestHold('Untouched period uncertain/ineligible')
    preserve(root,True);tests=run_tests(root)
    # Gate proofs are part of the actual test names, not a manually edited flag.
    required=['test_reader_refuses_without_ready','test_manual_ready_flag_cannot_authorize','test_real_three_X1_P2_parity','test_new_time_adapters_match_original','test_causal_prefix_all_replans']
    if any(not any(n.startswith(k) for n in tests['test_names']) for k in required):raise PretestHold('Missing critical gate tests')
    bind=binding(root)
    extra=[root/'CryptoCrossImpact_Research_Specification_v1_2026-10-27.md',root/'data/registry/source_manifest.json',
        root/'configs/stage04_policies.yaml',out/'development_selection.json',out/'holdout_eligibility.json',out/'pretest_tests.json',
        out/'pretest_pytest.xml',out/'pilot_parity.json',out/'development_output_audit.json']
    if (out/'reviewed_audit_fix.json').exists():
        extra+=[out/'reviewed_audit_fix.json']+list((out/'provenance').glob('before_*'))
    bind.update({str(p.relative_to(root)):sha256(p) for p in extra})
    for p in (root/'tests').glob('test_*.py'):bind[str(p.relative_to(root))]=sha256(p)
    lock=dict(status='FROZEN_X2X3_PROTOCOL',utc=utcnow(),bindings=bind,settings=config(root),selection=selection,
        evidence=dict(development_complete=736,eligibility='ELIGIBLE',tests_passed=tests['passed'],source_manifest=sha256(root/'data/registry/source_manifest.json')),
        funding_excluded=True,source_values_unopened=True)
    path=out/'pretest_lock.json'
    if path.exists():
        if json.loads(path.read_text())['bindings']!=bind:raise PretestHold('Existing immutable lock differs')
    else:save(path,lock)
    ready=dict(status='PRETEST_READY_X2X3',utc=utcnow(),lock_sha256=sha256(path),holdout=config(root)['holdout_start'],end=config(root)['holdout_end'])
    ready['digest']=digest(ready)
    rpath=out/'PRETEST_READY_X2X3.json'
    if not rpath.exists():save(rpath,ready)
    (root/'docs/extensions/x2x3_PRETEST_READY_v1.md').write_text('# X2+X3 pretest readiness\n\nVerified tests, complete development/selection/output audit and untouched eligibility passed before source access.\n\nLock SHA256: `'+sha256(path)+'`.\n\nScope: July–September2026, funding-excluded modeled cost and observed overload diagnostics; no causal/live fill claim.\n')
    return validate_ready(root)


def validate_ready(root):
    root=Path(root);out,_=paths(root)
    try:
        cached=_READY_CACHE.get(str(root.resolve()))
        if cached is not None:
            current=tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in cached['files'])
            if current==cached['stats']:return cached['ready']
        ready=json.loads((out/'PRETEST_READY_X2X3.json').read_text());lockpath=out/'pretest_lock.json';lock=json.loads(lockpath.read_text())
        if ready['status']!='PRETEST_READY_X2X3' or digest({k:v for k,v in ready.items() if k!='digest'})!=ready['digest'] or sha256(lockpath)!=ready['lock_sha256']:raise PretestHold('Invalid ready hash/receipt')
        if lock['evidence']['development_complete']!=736 or lock['evidence']['tests_passed']<230 or lock['evidence']['eligibility']!='ELIGIBLE' or not lock['funding_excluded']:raise PretestHold('Incomplete readiness evidence')
        for name,h in lock['bindings'].items():
            if sha256(root/name)!=h:raise PretestHold('Frozen binding changed: '+name)
        tests=json.loads((out/'pretest_tests.json').read_text())
        if tests['failures'] or tests['returncode'] or tests['passed']<230:raise PretestHold('Invalid test results')
        if sha256(out/'pretest_pytest.xml')!=tests['junit_sha256']:raise PretestHold('JUnit changed')
        files=[out/'PRETEST_READY_X2X3.json',lockpath]+[root/n for n in lock['bindings']]
        _READY_CACHE[str(root.resolve())]=dict(files=files,stats=tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in files),ready=ready)
        return ready
    except (OSError,KeyError,ValueError,TypeError) as exc:raise PretestHold('PRETEST_HOLD_X2X3: '+str(exc)) from exc
