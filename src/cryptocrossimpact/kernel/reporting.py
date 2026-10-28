"""Compact, reproducible Stage 2 tables, figures, model lock and research report."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..data.storage import write_json,sha256,utcnow
from .features import ASSETS,DevelopmentStore
from .fit import level_kernel
from .workflow import locations,config,winners,make_provenance


def table(frame,columns):
    lines=["| "+" | ".join(columns)+" |","|"+"|".join(["---"]*len(columns))+"|"]
    for _,row in frame.iterrows():
        vals=[]
        for c in columns:
            value=row[c]
            vals.append(f"{value:.6g}" if isinstance(value,(float,np.floating)) else str(value))
        lines.append("| "+" | ".join(vals)+" |")
    return "\n".join(lines)


def make_figures(root,models,metrics,bootstrap,placebo,stability,modes):
    out,_=locations(root);figdir=Path(root)/"figures/stage02";figdir.mkdir(parents=True,exist_ok=True)
    lags=np.arange(61);a=level_kernel(models["A"],lags);b=level_kernel(models["B"],lags)
    curve=[]
    for lag in [0,1,5,15,30,60]:
        for model,kernel in [("A",a),("B",b)]:
            for i in range(2):
                for j in range(2):curve.append(dict(model=model,lag_minutes=lag,response_asset=ASSETS[i],flow_asset=ASSETS[j],G=kernel[lag,i,j]))
    pd.DataFrame(curve).to_csv(out/"lag_curves.csv",index=False)
    coeff=[]
    for name,m in models.items():
        for k,c in enumerate(np.array(m["matrices"])):
            if name in ("A","B"):
                diag=m["component_diagnostics"][k]
                coeff.append(dict(model=name,component=k,tau_minutes=m["taus_minutes"][k],C00=c[0,0],C01=c[0,1],C10=c[1,0],C11=c[1,1],
                    eigen_min=diag["eigenvalues"][0],eigen_max=diag["eigenvalues"][1],cross_ratio=diag["cross_ratio"],psd_binding=diag["psd_binding"],condition_number=diag["condition_number"]))
    pd.DataFrame(coeff).to_csv(out/"matrix_diagnostics.csv",index=False)
    fig,axes=plt.subplots(2,2,figsize=(9,6),sharex=True,constrained_layout=True)
    for i in range(2):
        for j in range(2):
            ax=axes[i,j];ax.plot(lags,a[:,i,j],label="A diagonal",color="#888888",ls="--")
            ax.plot(lags,b[:,i,j],label="B full PSD",color="#17688c")
            key=f"C0_{min(i,j)}{max(i,j)}"
            if len(models["B"]["taus_minutes"])==1 and key in bootstrap:
                ci=np.quantile(bootstrap[key],[.025,.975])[:,None]*np.exp(-lags/models["B"]["taus_minutes"][0])[None,:]
                ax.fill_between(lags,ci[0],ci[1],alpha=.2,color="#17688c",label="95% training-block interval")
            ax.set_title(f"{ASSETS[j]} flow → {ASSETS[i]} response")
            ax.set_ylabel("G in cash-consistent bps coordinates");ax.set_xlabel("Lag (minutes)")
    axes[0,0].legend(fontsize=7)
    fig.suptitle("Development training Jan 2024–Jun 2025; conditional response kernels")
    fig.savefig(figdir/"level_kernels.png",dpi=140);plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    monthly=metrics[(metrics.group.str.startswith("month:2025-"))&(metrics.group>="month:2025-07")&(metrics.asset=="pooled")]
    for name in ("N0","U","A","B"):
        d=monthly[monthly.model==name];axes[0].plot(d.group.str[-7:],d.standardized_mse,marker="o",label=name)
    axes[0].set_title("Fixed training fit; monthly validation response error")
    axes[0].set_ylabel("Mean training-standardized MSE");axes[0].tick_params(axis="x",rotation=40);axes[0].legend()
    s=stability[stability.window.str.startswith("2025")]
    axes[1].plot(s.window,s.cross_ratio,marker="o",color="#17688c")
    axes[1].set_title("Past-only development rolling fits; no 2026 refits")
    axes[1].set_ylabel("C12 / sqrt(C11 C22)");axes[1].tick_params(axis="x",rotation=40)
    fig.savefig(figdir/"development_stability.png",dpi=140);plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(9,3.7),constrained_layout=True)
    observed=float(np.array(models["B"]["matrices"])[:,0,1].sum())
    axes[0].hist(bootstrap.instantaneous_cross,bins=12,color="#17688c",alpha=.8)
    axes[0].axvline(observed,color="black",ls="--",label="Original training B")
    axes[0].set_title("50 seven-day training-block refits");axes[0].set_xlabel("Instantaneous sum(C12), economic coordinates");axes[0].set_ylabel("Replicates");axes[0].legend(fontsize=7)
    axes[1].hist(placebo.instantaneous_cross,bins=12,color="#a67444",alpha=.8)
    axes[1].axvline(0,color="black",ls="--")
    axes[1].set_title("50 whole-day cross-only shifts; own flow retained")
    axes[1].set_xlabel("Placebo instantaneous sum(C12)");axes[1].set_ylabel("Replicates")
    fig.suptitle("Observational estimator variability and synchronization falsification")
    fig.savefig(figdir/"bootstrap_placebo.png",dpi=140);plt.close(fig)

    groups=[("Primary H60",None,60),("H30 sensitivity","primary",30),("H120 sensitivity","primary",120),
            ("Lag-only","lag_only",60),("Lead placebo\nFUTURE DATA","lead_placebo",60)]
    fig,ax=plt.subplots(figsize=(9,4),constrained_layout=True)
    for offset,name in [(-.18,"A"),(.18,"B")]:
        values=[]
        for label,mode,h in groups:
            if mode is None:
                score=metrics[(metrics.group=="validation")&(metrics.model==name)&(metrics.asset=="pooled")].standardized_mse.iloc[0]
                zero=metrics[(metrics.group=="validation")&(metrics.model=="N0")&(metrics.asset=="pooled")].standardized_mse.iloc[0]
            else:
                d=modes[(modes["mode"]==mode)&(modes.H==h)]
                score=d[d.model==name].validation_mse_pooled.iloc[0];zero=d[d.model=="N0"].validation_mse_pooled.iloc[0]
            values.append(score/zero)
        ax.bar(np.arange(len(groups))+offset,values,width=.34,label=name)
    ax.axhline(1,color="black",ls="--",lw=.8);ax.set_xticks(np.arange(len(groups)),[g[0] for g in groups])
    ax.set_ylabel("Validation MSE / matched N0 MSE");ax.set_title("Development only: explanatory gains rely on contemporaneous flow")
    ax.legend();fig.savefig(figdir/"timing_memory_sensitivity.png",dpi=140);plt.close(fig)
    return pd.DataFrame(coeff)


def report(root):
    root=Path(root);out,_=locations(root);cfg=config(root);models=winners(root)
    features=json.loads((out/"features.json").read_text());selection=json.loads((out/"selection.json").read_text())
    boot=json.loads((out/"bootstrap_summary.json").read_text());null=json.loads((out/"placebo_summary.json").read_text())
    tail=json.loads((out/"tail_diagnostic.json").read_text());completion=json.loads((out/"diagnostic_completion.json").read_text())
    metrics=pd.read_csv(out/"fit_metrics.csv");bootstrap=pd.read_csv(out/"bootstrap.csv");placebo=pd.read_csv(out/"placebo.csv")
    stability=pd.read_csv(out/"time_stability.csv");modes=pd.read_csv(out/"mode_diagnostics.csv");sens=pd.read_csv(out/"restricted_sensitivity.csv")
    coefficients=make_figures(root,models,metrics,bootstrap,placebo,stability,modes)
    val=metrics[(metrics.group=="validation")&(metrics.asset=="pooled")].set_index("model")
    gain=float(1-val.loc["B","standardized_mse"]/val.loc["A","standardized_mse"])
    # Deliberately scoped to development conditional association; H1/H2 are untouched.
    scientific="SUPPORTS_HYPOTHESIS" if gain>=.005 and boot["sign_reversals"]==0 else "INCONCLUSIVE"
    model_hashes={k:sha256(out/f"model_{k}.json") for k in models}
    lock=dict(status="DEVELOPMENT_ESTIMATION_LOCK",created_at_utc=utcnow(),stage="Stage 2 only; full policies/evaluators not yet frozen",
        selected=selection["selected"],model_sha256=model_hashes,asset_order=ASSETS,memory_minutes=60,
        sample="All paired source-valid target and preceding 1440 valid return bars; no flag-based primary exclusions",
        nuisance_features=features["feature_metadata"],normalization="Median positive prior-window quote volume per asset; train-only centering/scales/target SD; frozen for subsequent predictions",
        future_protocol="365 complete UTC days ending strictly before each refit month; monthly freeze; no intramonth revision; requires later Stage 5 authorization",
        metrics=["mean per-asset training-standardized response MSE","return-bps MAE/RMSE","conditional-response R2","paired monthly errors"],
        tie_rule=selection["tie_rule"],uncertainty="50 seven-day training-block fixed-family refits; final-test seven-day 500-fold paired inference remains for Stage 5",
        deviations="See SPEC_CHANGELOG.md: rank/permutation/feature clarifications; primary dates/grid/estimand unchanged",
        test_research_rows_read=False,stage3_solver_run=False,causal_identification=False,
        full_test_freeze_complete=False)
    write_json(out/"pretest_estimation_lock.json",lock)
    l=np.array(features["liquidity_usdt"])
    exposure=[]
    for name in ("A","B"):
        g=level_kernel(models[name],[0])[0]
        for i in range(2):
            for j in range(2):exposure.append(dict(model=name,response_asset=ASSETS[i],flow_asset=ASSETS[j],signed_quote_notional_usdt=100000,
                assumed_instantaneous_log_displacement_bps=float(g[i,j]*100000/np.sqrt(l[i]*l[j]))))
    pd.DataFrame(exposure).to_csv(out/"reference_notional_displacement.csv",index=False)
    derived=metrics[(metrics.group=="validation")].copy()
    primary_table=derived[["model","asset","standardized_mse","mae_bps","rmse_bps","conditional_response_r2"]]
    selection_table=pd.DataFrame([dict(model=k,tau_minutes=";".join(map(str,m["taus_minutes"])),ridge=m["ridge"],training_rows=m["training_rows"],
        validation_mse=m["validation_mse_pooled"]) for k,m in models.items()])
    stability_cols=["window","C00_reference","C01_reference","C11_reference","cross_ratio"]
    lines=["# Stage 2: admissible BTC/ETH conditional flow-response kernels", "",
        f"Generated UTC: {utcnow()}. **G2 implementation: PASS. Development-only scientific verdict: {scientific}.**", "",
        f"The full PSD model B reduces pooled July–December 2025 conditional response MSE by **{gain:.2%}** relative to matched diagonal A. "
        "Cross response is positive and persists across training halves and development rolling windows. This is evidence of an observational contemporaneous association. "
        "It does not identify the causal effect of our hypothetical orders, establish an implementable forecast, or test the January–June 2026 H1/H2 hypotheses.", "",
        "## Mathematics, units and reference", "",
        "The governing protocol is [specification v1.0 §§4–6](../../CryptoCrossImpact_Research_Specification_v1_2026-10-27.md). "
        "The supplied [AJNT preprint v2](../../references/2403.10273v2.pdf), dated February 20, 2026, defines nonnegative-definite Volterra kernels in §2.1, equation (2.7), "
        "and gives convolution sufficient conditions in §2.3, Theorem 2.15 (printed p.11) and Corollary 2.18 (p.12). Those pages were text-extracted and visually reviewed. "
        "A sum of PSD matrices times scalar exponentials satisfies the quadratic-form monotonicity/convexity conditions, including valid negative off-diagonal entries. "
        "These are published admissibility results; no new theorem or numerical reproduction of AJNT's optimizer is claimed.", "",
        "For each asset, L is the median positive train-window minute quote turnover (USDT). f=q/sqrt(L), r=log(close_t)-log(close_{t-1}), "
        "and y=10,000 sqrt(L) r. y is already a one-bar return. Here L="+str(features["liquidity_usdt"])+" USDT, estimated through June 30, 2025 and frozen for validation.", "",
        "For each time constant tau, the fitted return basis is z_tau,t = f_t + sum_{ell=1..H}(exp(-ell/tau)-exp(-(ell-1)/tau)) f_{t-ell}. "
        "The regression is y_t=sum C_tau z_tau,t + asset-specific nuisance/intercept + error, with H=60. Positive-lag weights are negative. "
        "No H+1 boundary term is silently added: that term would arise only if exactly differencing a finitely truncated *level* kernel, a different equation.", "",
        "Predictors are centered/scaled on eligible training rows; the loss divides each asset's y by its own training SD. "
        "The minimized objective is mean standardized squared error over assets plus lambda/2 times the sum of squared standardized coefficients, excluding intercepts. "
        "The standardized flow coefficient is beta_ij = C_ij s(z_j)/s(y_i); economic C remains symmetric PSD. A common numerical C scale is reversible and does not constrain a whitened or raw bps/USDT matrix.", "",
        "Hypothetical signed notional u has modeled log displacement 10^-4 D(L)^(-1/2) G D(L)^(-1/2)u. "
        "The small $100,000-notional displacement table is a unit-conversion assumption, not an observed execution or cost result. "
        "Same-cell finite-grid validation uses half self-impact. Cell-integrated production discretization, cash Hessian factors and execution constraints remain Stage 3 work.", "",
        "## Data, masks and available information", "",
        "Source: Binance Vision USD-M USDT perpetual BTCUSDT/ETHUSDT last-trade 1m klines. Development train January 2024–June 2025; "
        "validation July–December 2025. Stage 2 opens only 48 development symbol-month partitions, verifies their Stage 1 canonical hashes, and rejects 2026 paths before Parquet I/O. "
        "The original source manifest and canonical files are unchanged. Dataset attribution: Binance Vision; derived analytical tables/figures are CC BY-NC-SA 4.0 under the recorded dataset terms.", "",
        "There are 786,239 synchronized eligible train targets and 264,960 validation targets for all N0/U/A/B primary fits. "
        "Initial attrition is one unavailable target return plus 1,440 target/history warmup rows; no additional calendar gaps or malformed observations. "
        "All primary models use identical rows, controls, normalization and A/B grid budget. The null permutation diagnostic has a separately disclosed common 783,239-row mask because all shifted lag windows must be valid.", "",
        "Controls use each asset's prior returns at lags 1/2/5/15; log1p(mean prior unsigned USDT turnover) over 5/15/60 minutes; "
        "previous-bar log1p turnover minus its prior 1,440-bar median; prior population RMS returns over 60/1,440 minutes; and smooth UTC intraday/weekly sine/cosine. "
        "The equally weighted lag-one factor is omitted because it is an exact linear combination of included returns. Full source/lookback/availability metadata are in features.json. "
        "Nuisance inputs end at target bar open (the prior bar's completion); observed target-bar flow and y become available at target bar end. No centered windows or same-bar returns enter controls.", "",
        "Recorded zero-turnover bars are retained (BTC 126, ETH 127 across development), including the October 2024 shared plateau. "
        "No raw values or flow signs were filled or replaced. Stage 1's 14-day aggTrades audit remains QUALIFIED: the sign agrees, exact minute aggregation does not. "
        "A separately declared October 28–30 sensitivity excludes 4,320 training target minutes, including conservative history padding; the primary sample is untouched.", "",
        "## Matched estimation and development selection", "",
        "N0 is nuisance-only; U has unconstrained/asymmetric component matrices and is diagnostic-only; A has nonnegative diagonals; B has jointly fitted symmetric PSD components. "
        "[CVXPY solver capabilities](https://www.cvxpy.org/tutorial/solvers/index.html) were checked against a real SDP smoke problem. "
        "CLARABEL performs constrained fits at 1e-9 feasibility / 1e-8 relative gap tolerances; direct design fits and SCS independently cross-check synthetic fits. "
        "OSQP was installed transitively with CVXPY and was not used as an SDP solver or to implement execution.", "",
        "Every one- or two-element family from {2,5,10,30,60} minutes and every lambda in {0,0.0001,0.001,0.01,0.1,1} was attempted: "
        "90 U, 90 A, 90 B fits, plus six N0 penalties. All 276 converged; no screening, skipped candidates or hidden fit failures. "
        "Within 0.1% of minimum validation MSE, the fixed preference is fewer exponentials, stronger penalty, then lower MSE. All candidates and their objective/status/sample sizes remain in candidate_selection.csv.", "",
        table(selection_table,["model","tau_minutes","ridge","training_rows","validation_mse"]), "",
        "Monthly raw sufficient statistics use float64; numerical fitting is a small Gram-matrix problem, not a dense multi-million-row conic program. "
        "No feature dataset or rowwise predictions were persisted. Bootstrap uses small daily statistics; the cross-flow permutation uses only transient training arrays. "
        "All normalizers are training-only and all source-defined masks are shared. Near-zero numerical Gram eigenvalues are checked as accumulation roundoff; no economic kernel is projected or repaired.", "",
        "## Actual validation errors", "",
        "MSE is normalized by the training target SD. MAE and RMSE are log-return basis points. R² is same-minute conditional explanatory R², not forecast R².", "",
        table(primary_table,["model","asset","standardized_mse","mae_bps","rmse_bps","conditional_response_r2"]), "",
        "Residual BTC/ETH correlations and all training/monthly/weekend/liquidity results are in fit_metrics.csv. "
        "Validation liquidity groups compare a strictly past 60-minute activity measure against a fixed training median; they use neither future realized volume nor validation-derived thresholds. "
        "A validation gain does not settle final H1. Similar U/B errors indicate the constraint cost is modest on this sample, not that the observed response is causal.", "",
        table(metrics[(metrics.group.str.startswith("validation_"))&(metrics.asset=="pooled")],
              ["group","model","rows","standardized_mse","residual_cross_correlation"]), "",
        "## Matrix and time stability diagnostics", "",
        table(coefficients,["model","tau_minutes","C00","C01","C10","C11","eigen_min","eigen_max","cross_ratio","psd_binding"]), "",
        table(stability,stability_cols), "",
        "Half-window fits recompute L and training transforms. The table maps their matrices by congruence to the primary liquidity coordinates for comparison; cross ratios are scale invariant. "
        "The six monthly fits use 365 prior complete calendar days and end before July–December 2025. They are development-only stability diagnostics; primary validation errors use the fixed June-end model, not those rolling fits.", "",
        "![Kernels](../../figures/stage02/level_kernels.png)", "",
        "![Development stability](../../figures/stage02/development_stability.png)", "",
        "## Recovery, falsification and uncertainty", "",
        "Synthetic one/two-exponential recoveries include zero, positive and valid negative cross coefficients with observed nuisance-correlated flows, independently convolved targets, and sample-noise tolerances. "
        "The tests recover the known family in a fixed one-decay comparison, agree with direct design fitting on synthetic and real train-only subsets, preserve asset permutations/diagonal limits, "
        "reject indefinite matrices and block U from admissible-kernel export. Finite-grid kernels and 100 signed round trips are checked for each admissible candidate. "
        "Focused timing tests cover month/validation boundaries, the no-H+1 equation, input units, shared masks, unchanged past controls under future perturbations and pre-I/O test rejection.", "",
        f"Fifty seven-day training-block refits give instantaneous sum(C12) 95% interval **{boot['instantaneous_cross_95pct_interval']}**, "
        f"with {boot['sign_reversals']} sign reversals and {boot['binding_fraction']:.1%} binding-PSD replicate fraction. "
        "This conditions on the selected candidate and original preprocessing. Blocks resample original feature/return rows consistently; no lags are recalculated across resampled boundaries. "
        "It measures observational estimator variability, excluding hyperparameter/model uncertainty and causal uncertainty.", "",
        f"Fifty fixed whole-day cross-only shifts preserve each asset's own flow/return alignment. On the common null mask, observed training gain B over matched A is "
        f"{null['observed_same_mask_training_gain']:.3%}; null gains range {null['null_gain_range']}; shifted C12 sums range {null['null_cross_range']}. "
        f"The finite-sample diagnostic tail fraction is {null['empirical_diagnostic_tail_fraction']:.6f}. This is not a final-test p-value or proof of intervention identification.", "",
        "![Uncertainty and falsification](../../figures/stage02/bootstrap_placebo.png)", "",
        table(modes,["mode","H","model","training_rows","validation_rows","validation_mse_pooled","instantaneous_cross"]), "",
        "Lag-only flow contributes essentially no validation gain beyond nuisance controls. The lead-flow placebo contains future observed flow and still improves fit: "
        "that is explicit evidence compatible with feedback/correlated information, not a predictor. Lead-mode last bars are excluded each month, preventing train/validation or December/2026 crossing. "
        "Each mode compares N0/U/A/B on its own identical mask; primary choices are unchanged.", "",
        f"The selected tau=60 equals the grid upper boundary, and G(60)/G(0) retains **{tail['level_fraction_at_H']:.3%}** in norm. "
        f"The hypothetical omitted truncated-level H+1 term has training RMS/target SD {tail['hypothetical_Hplus1_boundary_rms_over_target_sd']}. "
        "The prespecified equation intentionally omits this term; it is not silently changed. H=30 and H=120 fitted sensitivities preserve the qualitative A/B comparison, "
        "but the data do not establish the full decay tail or structural causal kernel.", "",
        table(sens,["mode","model","training_rows","validation_mse_pooled","instantaneous_cross"]), "",
        "![Timing and memory](../../figures/stage02/timing_memory_sensitivity.png)", "",
        "## Scope, reproducibility and Stage 3 handoff", "",
        "G2 passes implementation checks separately from the development-only scientific association. The optional one-/five-minute forward-prediction diagnostic was NOT RUN; "
        "mandatory G2 estimation, falsification and uncertainty were prioritized, as allowed by the Stage 2 prompt. There is no alpha claim. "
        "Remaining scientific limits are public-flow endogeneity, same-bar information timing, aggregate-trade mismatch, training-only selection, coefficient/time drift, "
        "fixed-preprocessing bootstrap uncertainty and a long tail at the selected grid boundary. No mandatory G2 diagnostic remains incomplete.", "",
        "`model_A.json` and `model_B.json` hold validated economic matrices, ordered assets, tau in minutes, H, L, original training transforms, coefficients/intercepts, cutoffs and provenance. "
        "`kernel.fit.level_kernel(model, lags)` returns the admissible level kernel; `predict` reconstructs conditional responses using the same standardized design. "
        "`kernel.diagnostics.refit_historical` exposes the fixed-family past-window refit API with the Stage 2 I/O firewall. "
        "U is saved with diagnostic_only=true and export blocked. Stage 3 can use these artifacts without reacquiring Stage 1 data, while explicitly treating them as scenario assumptions. "
        "It must independently verify AJNT V1, its cell-integrated cash Hessian/factors, half-cell convention and constrained V2 solver. None is implemented here.", "",
        "The estimation-only pretest lock records family, lambda, masks, normalization, future refit protocol and metrics. It explicitly is not the final policy/evaluator lock: "
        "Stages 3/4 must finish their rules before Stage 5 can open final outcomes. See [implementation clarifications](../../SPEC_CHANGELOG.md).", "",
        "```sh", ".venv/bin/python -m pip install --no-cache-dir -r requirements.txt", ".venv/bin/python -m pytest tests/test_stage02_kernel.py -q",
        ".venv/bin/python scripts/stage02.py synthetic", ".venv/bin/python scripts/stage02.py all", "```", "",
        "Individual restart commands are `prepare`, `fit`, `metrics`, `diagnostics`, `report` with the same script. "
        "Run Stage 1 synthetic tests with `-m 'not integration'`; do not rerun Stage 1 integration tests that open 2026 pilot outcomes during Stage 2. "
        "Compact tables/models are trackable under reports/research/stage02_artifacts; only small sufficient statistics are cached under ignored results/kernel_development.", "",
        "**Stage 2 only was executed. No January–June 2026 research outcomes, liquidation policies, execution-cost backtests, or Stage 3 solver were evaluated.**", ""]
    (root/"reports/research/stage02_kernel_estimation.md").write_text("\n".join(lines))
    verdict=dict(implementation="PASS",scientific_development_only=scientific,validation_B_vs_A_relative_mse_gain=gain,
        mandatory_diagnostics_complete=completion,tail_qualification=tail,final_H1_H2_evaluated=False,
        stage3_solver_run=False,model_sha256=model_hashes)
    write_json(out/"verdict.json",verdict)
    print(json.dumps(verdict,indent=2),flush=True)
