"""Approved ex-funding Stage 5: preflight/freeze → chronological OOS → robustness."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"data/tmp/matplotlib"))
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
sys.path.insert(0,str(ROOT/"src"))


def run_tests():
    import subprocess,xml.etree.ElementTree as ET
    from cryptocrossimpact.evaluation.v2_common import locations,numerical_sources,save
    from cryptocrossimpact.data.storage import sha256,utcnow
    out,_=locations(ROOT);env=os.environ.copy();env["CCI_PRETEST_ONLY"]="1"
    files=["tests/test_stage01.py","tests/test_stage02_kernel.py","tests/test_stage03_execution.py","tests/test_stage04_policies.py","tests/test_stage05_evaluation.py","tests/test_stage05_v2.py"]
    cmd=[str(ROOT/".venv/bin/python"),"-m","pytest",*files,"-m","not integration","-q",f"--junitxml={out/'pretest_pytest.xml'}"]
    result=subprocess.run(cmd,cwd=ROOT,env=env)
    if result.returncode:raise RuntimeError("Pretest pytest failed; outcomes remain closed")
    suites=list(ET.parse(out/"pretest_pytest.xml").getroot().iter("testsuite"))
    save(out/"test_results_v2.json",dict(utc=utcnow(),passed=sum(int(s.attrib["tests"]) for s in suites),failed=0,deselected_integration=2,
        command=cmd,bindings={str(p.relative_to(ROOT)):sha256(p) for p in numerical_sources(ROOT)+[ROOT/f for f in files]}))


def main():
    import argparse,resource,time,subprocess,importlib.metadata
    from cryptocrossimpact.evaluation.v2_common import locations,save,numerical_sources,SCOPE
    from cryptocrossimpact.evaluation.v2_protocol import prepare,freeze,validate_ready
    from cryptocrossimpact.data.storage import sha256,utcnow,PublicSource
    from cryptocrossimpact.data.pipeline import load_config
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("command",choices=["prepare","preflight","freeze","primary","summarize","robustness","report","all"])
    args=p.parse_args();out,_=locations(ROOT);start=utcnow();clock=time.monotonic();status="FAILED"
    guard=PublicSource(ROOT,load_config(ROOT));before=guard.guard(500_000_000)
    try:
        if args.command in ("prepare","preflight"):prepare(ROOT)
        if args.command=="preflight":run_tests()
        if args.command=="freeze":freeze(ROOT)
        if args.command=="all":
            if (out/"pretest_ready_v2.json").exists():validate_ready(ROOT)
            else:prepare(ROOT);run_tests();freeze(ROOT)
        if args.command in ("primary","all"):
            from cryptocrossimpact.evaluation.v2_run import primary
            primary(ROOT)
            from cryptocrossimpact.evaluation.v2_summary import summarize
            summarize(ROOT,primary_only=True)
        if args.command in ("robustness","all"):
            from cryptocrossimpact.evaluation.v2_run import robustness
            robustness(ROOT)
        if args.command in ("summarize","report","all"):
            from cryptocrossimpact.evaluation.v2_report import summarize,report
            summarize(ROOT)
            if args.command in ("report","all"):report(ROOT)
        status="PASS"
    finally:
        save(out/f"run_{args.command}_v2.json",dict(status=status,command=args.command,utc=start,elapsed_seconds=time.monotonic()-clock,
            peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,project_bytes_before=before,project_bytes_after=guard.guard(),
            git_revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            dirty_status=subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),cost_scope=SCOPE,
            versions={n:importlib.metadata.version(n) for n in ["numpy","pandas","pyarrow","scipy","cvxpy","osqp","clarabel","pytest"]},
            source_bindings={str(f.relative_to(ROOT)):sha256(f) for f in numerical_sources(ROOT)},
            stage6_started=False,funding_included=False))


if __name__=="__main__":main()
