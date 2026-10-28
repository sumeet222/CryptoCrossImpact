"""Stage 2 entry point; refuses 2026 outcome partitions."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"data/tmp/matplotlib"))
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
sys.path.insert(0,str(ROOT/"src"))

from cryptocrossimpact.kernel.workflow import prepare,fit_grid,prediction_metrics


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["synthetic","prepare","fit","metrics","diagnostics","report","all"])
    args=parser.parse_args()
    import resource,time
    from cryptocrossimpact.data.pipeline import provenance,load_config
    from cryptocrossimpact.data.storage import PublicSource,write_json,sha256,utcnow
    from cryptocrossimpact.kernel.workflow import locations
    started=utcnow();clock=time.monotonic();out,_=locations(ROOT);status="FAILED"
    guard=PublicSource(ROOT,load_config(ROOT));before=guard.guard(1_000_000_000)
    try:
        if args.command=="synthetic":
            from cryptocrossimpact.kernel.diagnostics import synthetic_recovery
            synthetic_recovery(ROOT)
        if args.command in ("prepare","all"):prepare(ROOT)
        if args.command in ("fit","all"):fit_grid(ROOT)
        if args.command in ("metrics","all"):prediction_metrics(ROOT)
        if args.command in ("diagnostics","all"):
            from cryptocrossimpact.kernel.diagnostics import run_diagnostics
            run_diagnostics(ROOT)
        if args.command in ("report","all"):
            from cryptocrossimpact.kernel.reporting import report
            report(ROOT)
        status="PASS"
    finally:
        run=provenance(ROOT,load_config(ROOT))
        run.update(stage="Stage 2 development only",command=args.command,status=status,started_at_utc=started,
            elapsed_seconds=time.monotonic()-clock,project_bytes_before=before,project_bytes_after=guard.guard(),
            peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            stage02_config_sha256=sha256(ROOT/"configs/stage02_kernel.yaml"),
            source_manifest_sha256=sha256(ROOT/"data/registry/source_manifest.json"),
            final_outcome_scoring_performed=False,model_ids=["N0","U","A","B"],evaluator_ids=[])
        write_json(out/f"run_{args.command}.json",run)


if __name__=="__main__":main()
