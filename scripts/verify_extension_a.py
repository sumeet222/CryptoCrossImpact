#!/usr/bin/env python3
"""Full regression with Stage A scope: exclude one eager inherited2026 loader.

All original test files remain unchanged. The corresponding Stage A real-asof
B/E1 equivalence test uses only prepared2024–2025 statistics and reader logs.
"""
from pathlib import Path
import subprocess,sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cryptocrossimpact.stage_a.common import paths,save,binding
from cryptocrossimpact.data.storage import sha256,utcnow
root=Path(__file__).resolve().parents[1];out,_=paths(root)
names=['test_extension_a.py','test_extension_x1.py','test_extension_x2x3.py','test_stage01.py','test_stage02_kernel.py','test_stage03_execution.py','test_stage04_policies.py','test_stage05_evaluation.py','test_stage05_v2.py']
cmd=[str(root/'.venv/bin/python'),'-m','pytest',*['tests/'+n for n in names],'-m','not integration','-k','not real_asof_refit_adapter_matches_saved_development_models','-q','--junitxml='+str(out/'final_pytest.xml')]
r=subprocess.run(cmd,cwd=root,capture_output=True,text=True);(out/'final_stdout.txt').write_text(r.stdout+r.stderr)
suites=list(ET.parse(out/'final_pytest.xml').getroot().iter('testsuite'));count=sum(int(s.attrib.get('tests',0)) for s in suites);bad=sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in suites)
save(out/'final_tests.json',dict(utc=utcnow(),command=cmd,returncode=r.returncode,passed=count-bad,failures=bad,junit_sha256=sha256(out/'final_pytest.xml'),code=binding(root),test_files_sha256={n:sha256(root/'tests'/n) for n in names},wrapper_sha256=sha256(Path(__file__)),scope='Stage A inputs and new real-asof parity2024–2025 only;2 original integration tests and1 eager inherited2026-loader case excluded; original tests unchanged'))
print(r.stdout+r.stderr,flush=True)
if r.returncode or bad or count<280:raise SystemExit(1)
