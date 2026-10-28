"""Stage 5 blocked pretest checkpoint; reviews saved funding probes, no scorer."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))


def main():
    import argparse,json,resource,time,subprocess,importlib.metadata
    from cryptocrossimpact.data.storage import sha256,utcnow,write_json
    from cryptocrossimpact.evaluation.preflight import preflight,PretestHold
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["preflight","all"])
    args=parser.parse_args();clock=time.monotonic();started=utcnow()
    try:result=preflight(ROOT)
    except PretestHold as exc:
        result=dict(status="PRETEST HOLD",implementation="BLOCKED",blocker=str(exc),test_outcomes_unopened=True,stage6_started=False)
    out=ROOT/"reports/research/stage05_artifacts";out.mkdir(exist_ok=True)
    write_json(out/"preflight.json",result)
    files=[ROOT/"scripts/stage05.py",ROOT/"tests/test_stage05_evaluation.py"]+list((ROOT/"src/cryptocrossimpact/evaluation").glob("*.py"))
    write_json(out/f"run_{args.command}.json",dict(utc=started,status=result["status"],command=args.command,
        elapsed_seconds=time.monotonic()-clock,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        versions={p:importlib.metadata.version(p) for p in ["numpy","pandas","pyarrow","scipy","cvxpy","pytest"]},
        git_branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip(),
        git_revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        dirty_status=subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),
        source_bindings={str(p.relative_to(ROOT)):sha256(p) for p in files},
        prompt_sha256=sha256(ROOT/"prompts/CryptoCrossImpact_Codex_Stage05_OOS_Evaluation_and_Robustness_Prompt_2026-10-27.md"),
        spec_sha256=sha256(ROOT/"CryptoCrossImpact_Research_Specification_v1_2026-10-27.md"),
        predecessor_lock_sha256=sha256(ROOT/"configs/stage05_pretest_lock.yaml"),
        canonical_rows_loaded=0,final_test_outcomes_opened=False,scored_episodes=0))
    print(json.dumps({k:result.get(k) for k in ["status","implementation","H1","H2","scored_2026_episodes","test_outcomes_unopened"]}))
    # 'all' cannot silently skip the failed funding gate or create readiness.
    return 2


if __name__=="__main__":sys.exit(main())
