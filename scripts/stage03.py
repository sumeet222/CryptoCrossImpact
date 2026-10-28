"""Stage 3: paper deterministic benchmark + synthetic constrained QP only."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"data/tmp/matplotlib"))
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
sys.path.insert(0,str(ROOT/"src"))

from cryptocrossimpact.execution.verification import paper,synthetic,models_smoke,location,save


def main():
    import argparse,resource,time
    from cryptocrossimpact.data.pipeline import provenance,load_config
    from cryptocrossimpact.data.storage import PublicSource,sha256,utcnow
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["paper","synthetic","models-smoke","report","all"])
    args=parser.parse_args();out=location(ROOT);started=utcnow();clock=time.monotonic();status="FAILED"
    guard=PublicSource(ROOT,load_config(ROOT));before=guard.guard(300_000_000)
    try:
        if args.command in ("paper","all"):paper(ROOT)
        if args.command in ("synthetic","all"):synthetic(ROOT)
        if args.command in ("models-smoke","all"):models_smoke(ROOT)
        if args.command in ("report","all"):
            from cryptocrossimpact.execution.reporting import report
            report(ROOT)
        status="PASS"
    finally:
        run=provenance(ROOT,load_config(ROOT))
        run.update(stage="G3 mathematical verification only",command=args.command,status=status,started_at_utc=started,
            elapsed_seconds=time.monotonic()-clock,project_bytes_before=before,project_bytes_after=guard.guard(),
            peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            prompt_sha256=sha256(ROOT/"prompts/CryptoCrossImpact_Codex_Stage03_Mathematical_Execution_Solver_Prompt_2026-10-27.md"),
            stage03_config_sha256=sha256(ROOT/"configs/stage03_execution.yaml"),
            paper=dict(path="references/2403.10273v2.pdf",sha256=sha256(ROOT/"references/2403.10273v2.pdf"),version="arXiv v2 2026-02-20"),
            stage02_model_sha256={k:sha256(ROOT/f"reports/research/stage02_artifacts/model_{k}.json") for k in ("A","B")},
            source_identity="Binance futures/um 1m BTCUSDT/ETHUSDT; JSON metadata only",
            market_data_rows_loaded=0,final_outcome_scoring_performed=False,model_ids=["A","B"],evaluator_ids=[],
            conventions=dict(V1="paper Table1 collocation; independent exact-cell Galerkin/continuous exponential check",V2="exact_exponential_cells; .5 z'H z cash"),
            input_kind="paper dimensionless constants and explicitly synthetic forecasts/covariance; no observed execution prices")
        save(out/f"run_{args.command}.json",run)


if __name__=="__main__":main()
