"""Development schedule QA and a pending, outcome-blind Stage 5 protocol lock."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from .data.storage import sha256,utcnow
from .episodes import config
from .stage04 import paths,read_episodes,save
from .execution.reporting import markdown_table


def preservation(root):
    root=Path(root);out,_=paths(root);start=json.loads((out/"preservation_start.json").read_text())
    allowed="src/cryptocrossimpact/execution/solver.py";changed=[]
    for name,digest in start["sha256"].items():
        if name==allowed:continue
        if sha256(root/name)!=digest:changed.append(name)
    for name,stat in start["canonical_stat"].items():
        p=root/name
        if dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns)!=stat:changed.append(name)
    prior_solver=root/"results/stage04_development/provenance/stage03_solver_original.py"
    if sha256(prior_solver)!=start["sha256"][allowed]:changed.append("original solver preservation copy")
    result=dict(status="PASS" if not changed else "FAILED",protected_prior_files=len(start["sha256"])-1,
                canonical_stat_only_partitions=60,changed=changed,
                authorized_api_extension=allowed,original_solver_copy=str(prior_solver.relative_to(root)))
    save(out/"preservation_end.json",result)
    if changed:raise ValueError(f"Prior artifacts changed: {changed}")
    return result


def tables(root):
    root=Path(root);out,bulk=paths(root);episodes=read_episodes(root);records=[];forecast=[]
    for e in episodes:
        p=e.provenance
        records.append(dict(episode_id=e.episode_id,t0=str(e.t0),month=e.t0.strftime("%Y-%m"),history_rows=p["history_rows"],
            covariance_returns=p["covariance_returns"],latest_open=p["latest_open"],latest_available_at=p["latest_available_at"],
            btc_initial_usdt=e.initial[0],eth_initial_usdt=e.initial[1],cov00=e.covariance[0,0],cov01=e.covariance[0,1],cov11=e.covariance[1,1],
            jump_history_bars=p["diagnostic_jump_bars"],stale_history_bars=p["diagnostic_stale_bars"],input_hash=e.input_hash))
        for d in p["forecast_qa"]:
            forecast.append(dict(episode_id=e.episode_id,month=e.t0.strftime("%Y-%m"),asset=d["asset"],floor_usdt=d["floor_usdt"],
                floor_bins=d["floor_bins"],minimum_class_count=d["minimum_class_count"],zero_turnover_bars=d["zero_turnover_bars"],**d["class_bins"]))
    epi=pd.DataFrame(records);f=pd.DataFrame(forecast);epi.to_csv(out/"episode_registry.csv",index=False);f.to_csv(out/"forecast_qa.csv",index=False)
    diagnostics=pd.read_csv(out/"policy_diagnostics_development.csv")
    solved=set(diagnostics.episode_id)
    counts=epi.groupby("month").agg(eligible=("episode_id","size"),minimum_history_rows=("history_rows","min"),minimum_cov_returns=("covariance_returns","min"))
    counts["solved"]=epi.assign(solved=epi.episode_id.isin(solved)).groupby("month").solved.sum()
    counts["nominal"]=[pd.Period(m).days_in_month*4 for m in counts.index];counts["excluded"]=counts.nominal-counts.eligible
    counts=counts.reset_index();counts.to_csv(out/"monthly_coverage.csv",index=False)
    fairness=diagnostics.groupby("policy").agg(schedules=("policy","size"),terminal_max_usdt=("terminal_max_usdt","max"),
        normalized_residual_max=("normalized_physical_residual","max"),KKT_max=("stationarity","max"),
        decomposition_max=("decomposition_residual","max"),cap_binding_cells=("cap_binding_cells","sum"),
        twap_adjusted_cells=("twap_adjusted_cells","sum"),iterations_max=("iterations","max"),solve_seconds_mean=("solve_seconds","mean"))
    fairness=fairness.reset_index();fairness.to_csv(out/"policy_fairness.csv",index=False)
    # All six policies must have one common immutable input hash/beta per episode.
    grouped=diagnostics.groupby("episode_id")
    if not ((grouped.beta.nunique()==1).all() and (grouped.input_hash.nunique()==1).all() and (grouped.size()==6).all()):
        raise ValueError("Historical matched-policy identity failed")
    schedule=pd.read_parquet(bulk/"schedules_development.parquet")
    for asset in ("btc","eth"):
        mapping=epi.set_index("episode_id")[f"{asset}_initial_usdt"]
        schedule[f"{asset}_sale_fraction"]=schedule[f"{asset}_sales_usdt"]/schedule.episode_id.map(mapping)
        schedule[f"{asset}_remaining_fraction"]=schedule[f"{asset}_before_usdt"]/schedule.episode_id.map(mapping)
    aggregate=schedule.groupby(["policy","minute"])[[f"{a}_{c}" for a in ("btc","eth") for c in ("sale_fraction","remaining_fraction")]].mean().reset_index()
    aggregate.to_csv(out/"aggregate_schedule.csv",index=False)
    representative=schedule[schedule.episode_id=="20250707T0000Z"].copy()
    representative.to_csv(out/"representative_schedule.csv",index=False)
    return episodes,epi,f,counts,fairness,schedule,aggregate,representative


def figures(root,episodes,aggregate,representative):
    root=Path(root);figdir=root/"figures/stage04";figdir.mkdir(parents=True,exist_ok=True)
    e=next(e for e in episodes if e.episode_id=="20250707T0000Z")
    colors=dict(T0="#444444",T1="#ab76c3",T2="#319a7a",T3="#3878a9",T3B="#dc9e29",T4="#cc564a")
    fig,axes=plt.subplots(2,2,figsize=(11,6.5),constrained_layout=True)
    for i,asset in enumerate(("btc","eth")):
        for name,color in colors.items():
            d=representative[representative.policy==name]
            axes[i,0].plot(d.minute,d[f"{asset}_sales_usdt"]/1000,label=name,color=color,ls="--" if name in ("T1","T3B") else "-")
            terminal=d[f"{asset}_after_usdt"].iloc[-1]/e.initial[i]
            axes[i,1].plot(np.arange(61),np.r_[d[f"{asset}_remaining_fraction"],terminal],color=color)
        axes[i,0].plot(np.arange(60),.1*e.forecast[:,i]/1000,color="black",ls=":",label="shared forecast cap")
        axes[i,0].set_ylabel(f"{asset.upper()} sale (thousand USDT/min)");axes[i,1].set_ylabel(f"{asset.upper()} remaining / initial")
        for ax in axes[i]:ax.set_xlabel("Minutes since 2025-07-07 00:00 UTC")
    axes[0,0].legend(fontsize=8,ncol=2)
    fig.suptitle("Development only: predetermined first Monday, monthly as-of models; no outcome scoring")
    fig.savefig(figdir/"representative_episode.png",dpi=140);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),constrained_layout=True)
    for i,asset in enumerate(("btc","eth")):
        for name,color in colors.items():
            d=aggregate[aggregate.policy==name]
            axes[i].plot(d.minute,d[f"{asset}_remaining_fraction"],label=name,color=color,ls="--" if name in ("T1","T3B") else "-")
        axes[i].set_xlabel("Minutes since arrival");axes[i].set_ylabel(f"Mean {asset.upper()} inventory / initial")
    axes[0].legend(fontsize=8,ncol=2);fig.suptitle("July–December 2025: equal-episode schedule geometry, six matched policies")
    fig.savefig(figdir/"aggregate_schedules.png",dpi=140);plt.close(fig)
    # Four-arrival profile from the FIRST development day, chosen by calendar.
    first=episodes[:4];profile=[]
    for ep in first:
        for i,asset in enumerate(("BTCUSDT","ETHUSDT")):
            d=ep.provenance["forecast_qa"][i]
            profile.append(dict(t0=str(ep.t0),hour=ep.t0.hour,asset=asset,forecast_usdt=ep.forecast[0,i],floor_usdt=d["floor_usdt"],
                variance_per_minute=ep.covariance[i,i]))
    p=pd.DataFrame(profile);p.to_csv(root/"reports/research/stage04_artifacts/forecast_profile.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),constrained_layout=True)
    for asset,color in [("BTCUSDT","#3878a9"),("ETHUSDT","#cc564a")]:
        d=p[p.asset==asset]
        axes[0].plot(d.hour,d.forecast_usdt/1e6,"o-",label=f"{asset} forecast",color=color)
        axes[0].plot(d.hour,d.floor_usdt/1e6,"--",label=f"{asset} floor",color=color)
        axes[1].plot(d.hour,d.variance_per_minute*1e8,"o-",label=asset,color=color)
    axes[0].set_ylabel("Past-only turnover (million USDT/min)");axes[1].set_ylabel("Past-only one-minute variance (bp²)")
    for ax in axes:ax.set_xlabel("Arrival hour UTC, July 1 2025");ax.set_xticks([0,6,12,18]);ax.legend(fontsize=8)
    fig.suptitle("First development day: trailing 28d seasonal medians, positive floors and risk inputs")
    fig.savefig(figdir/"forecast_risk_inputs.png",dpi=140);plt.close(fig)


def report(root):
    root=Path(root);out,_=paths(root);preserve=preservation(root)
    episodes,epi,f,coverage,fairness,schedules,aggregate,representative=tables(root)
    figures(root,episodes,aggregate,representative)
    p=json.loads((out/"policies_development.json").read_text());smoke=json.loads((out/"policies_smoke.json").read_text())
    geom=pd.read_csv(out/"schedule_geometry_development.csv")
    summary=geom.groupby("contrast").agg(mean_rate_l2=("relative_rate_l2","mean"),max_rate_l2=("relative_rate_l2","max"),
        mean_inventory_difference=("maximum_inventory_difference_over_initial","mean"),maximum_inventory_difference=("maximum_inventory_difference_over_initial","max")).reset_index()
    summary.to_csv(out/"schedule_geometry_summary.csv",index=False)
    verdict=dict(implementation="PASS" if not p["failures"] else "QUALIFIED",stage_verdict="QUALIFIED",pretest_status="PRETEST_LOCK_PENDING",
        G4_OOS="NOT_RUN",scientific_hypotheses="NOT_EVALUATED",nominal_episodes=736,eligible=len(episodes),complete=p["complete_episodes"],
        policy_schedules=p["policy_schedules"],solver_failures=len(p["failures"]),test_outcomes_unopened=True,stage5_started=False,
        pending="Before test opening: funding preflight and E1 implementation validation on development data. Then strict-as-of E1 artifacts before each month scoring; no retuning",
        deterministic_replay=p["deterministic_replay_matches_prior"],preservation=preserve)
    save(out/"verdict.json",verdict)
    tests=json.loads((out/"test_results.json").read_text()) if (out/"test_results.json").exists() else None
    test_summary=(f"{tests['passed']} passed, {tests['failed']} failed; {tests['deselected_integration']} Stage 1 integration cases deselected to keep test outcomes closed. "
                  f"Stage 4: {tests['stage04_cases']} cases; prior-stage regressions: {tests['prior_stage_cases']}. "
                  "Exact command, test hashes and JUnit evidence are in stage04_artifacts/test_results.json and pytest.xml.") if tests else "Test evidence pending; no pass count inferred."
    text=f"""# Stage 4: causal historical episodes and matched development policies

Generated UTC: {utcnow()}. **Implementation {verdict['implementation']}; stage QUALIFIED / PRETEST_LOCK_PENDING.**
G4 OOS evaluation is NOT RUN. No economic hypothesis, shortfall or savings comparison was evaluated.
Stage 5 was not begun; January–June 2026 canonical observations were never opened.

## Scope, chronology and inputs

Reuse the [specification](../../CryptoCrossImpact_Research_Specification_v1_2026-10-27.md),
Stage 1 validated Binance USD-M perpetual trade-price minute bars, Stage 2 frozen
family (tau=60 minutes, ridge=1), and Stage 3 exact exponential-cell constrained
QP. The published AJNT signed terminal-penalty problem remains a separate verified
benchmark; no theorem extension is claimed. Data attribution: Binance Vision;
derived data summaries follow the recorded CC BY-NC-SA terms.

Arrival t0 includes the completed bar opening t0−1min (available exactly t0),
excluding the bar opening t0. Decisions are frozen/open-loop and contain no
alpha. Each history is the full paired [t0−28d,t0) UTC minute calendar, with all
valid source bars required. Missing, duplicate or invalid inputs exclude the
whole episode; diagnostic jumps/stale and verified zero turnover are retained.
No future-bar existence/value audit selects these Stage 4 schedules; Stage 5
will apply the locked mechanical evaluation-window QC independently of values.

Per-bin turnover Vhat (USDT) is the past hour-of-week median (minimum120), then
hour-of-day (minimum120), then overall median; floor=max(past positive 1st
percentile,1e-8 USDT). Covariance is sample/ddof1 of consecutive close log
returns wholly inside the window: 40319 pairs, minimum40000; no eigenvalue
clipping. Sigma is per minute; Stage 3 multiplies by delta once. P0 is the last
completed close, retained for later scoring only. No historical future-price
cost or realized-volume participation was computed here.

X0=0.02 sum Vhat per leg, caps=0.10 Vhat, 60 one-minute bins. Inventories and
sales use continuous reference USDT; no lot-size/fill reconstruction. Kappa=.001,
theta=1, fee=5bp, half-spread=1bp are assumptions; m=0. Common beta is computed
from full past covariance and capped closest-uniform TWAP, including pretrade
inventory. T2 retains this exact global beta while deciding with own variance.
All policies report full-covariance raw risk and risk preference separately.

## As-of kernels and matched policies

T0 closest capped TWAP; T1 forecast VWAP; T2 two independent A own-kernel QPs;
T3 joint A/full risk; T4 joint B/full risk; T3B diagonal of EACH B component,
same B tau/L/full risk. T4–T3 compares estimated families (A and B self terms
differ); T4–T3B isolates off-diagonal impact. The authorized clarification is in
[SPEC_CHANGELOG](../../SPEC_CHANGELOG.md). No baseline was relabeled.

Main diagnostics use six monthly as-of 365-complete-day fits. Existing B refits
are reused; six missing A fits were produced through refit_historical with the
same selected family/penalty. Every kernel retains its own fitted L, without
mixing coordinates. Original context can precede the target window for lag
features, but target labels and L lie inside it, ending before the month. All
365d windows have 525600 eligible fit rows. Full fit windows, L, C, hashes and
sources: [model_registry.csv](stage04_artifacts/model_registry.csv). The fixed
June-end models are a sensitivity on first UTC Monday's four arrivals each month
({p['fixed_model_sensitivity_episodes']} episodes); its schedule distances are
retained, not used for selection.

## Development coverage and forecast QA

The two-day smoke completed {smoke['complete_episodes']} episodes / {smoke['policy_schedules']} schedules.
Full development nominal=736; eligible={len(episodes)}; complete={p['complete_episodes']};
six-policy schedules={p['policy_schedules']}; primary scalar/joint QPs={p['scalar_and_joint_qp_solves']}.
Common policy failures={len(p['failures'])}; no unfavorable episode was dropped.

{markdown_table(coverage,list(coverage.columns))}

Across {len(f)*60} forecast asset-bins: hour-of-week={int(f.hour_of_week.sum())},
hour-of-day={int(f.hour_of_day.sum())}, overall={int(f.overall.sum())},
floored={int(f.floor_bins.sum())}. Minimum fine-class count={int(f.minimum_class_count.min())}.
Median initial inventory: BTC {epi.btc_initial_usdt.median():,.2f} USDT;
ETH {epi.eth_initial_usdt.median():,.2f} USDT. Windows containing diagnostic
jumps={int((epi.jump_history_bars>0).sum())}, stale flags={int((epi.stale_history_bars>0).sum())};
these are overlapping history counts, not independent anomalies/exclusions.
Verified zero turnover is retained and recorded in forecast_qa.csv.

All primary arrivals are at an hour boundary and T=60. An hour-of-week median
therefore gives a constant forecast within each primary episode, so T0 and T1
coincide by construction. This is a consequence of the approved simple forecast,
not a reason to tune it. Alternate 30/120-minute and cap smoke fixtures preserve
time-safe inputs and feasibility. Future mutation tests alter current/later bars
without changing forecasts, covariance, X0 or ANY of the six schedules.

![Forecast and risk QA](../../figures/stage04/forecast_risk_inputs.png)

## Fairness, solver and schedule geometry

{markdown_table(fairness,list(fairness.columns))}

Every complete episode has one exact shared input hash and beta across all six
policies. Feasibility tolerances are relative to each leg's USDT inventory;
terminal tolerance max(1e-6 X_i,1e-8 USDT); stricter normalized residual<=1e-7.
OSQP requires optimal and checked KKT/decomposition; no clipping, cap relaxation,
PSD repair or residual inventory concealment. Deterministic formula policies have
no QP KKT condition (their zero in table means not applicable). T2 iterations sum
two scalar solves. Own-model objectives in raw QA tables are heterogeneous and
are NEVER used as a policy ranking. No E0–E4 evaluator or P&L matrix was run.

{markdown_table(summary,list(summary.columns))}

These are rate/inventory geometry differences only, not costs or savings. The
representative episode is July7 00:00, fixed as the first UTC Monday before
inspection; the aggregate is equally weighted over all complete episodes.

![Predetermined episode](../../figures/stage04/representative_episode.png)

![Aggregate inventory geometry](../../figures/stage04/aggregate_schedules.png)

## Verification, preservation and handoff

Test evidence: {test_summary}
Two independent complete runs are required for the final deterministic replay
check; current recorded match={p['deterministic_replay_matches_prior']}.
Schedules are stored once in ignored results/stage04_development; compact source
tables and input/model IDs accompany them. Existing {preserve['protected_prior_files']}
protected prior files and all60 canonical stat snapshots are unchanged. The
sole previous-source edit adds optional risk_multiplier_override to the verified
QP, default unchanged; its original source is preserved and regression-tested.

[Versioned pretest protocol](../../docs/stage05_pretest_policy_evaluator_lock_v1.md)
and configs/stage05_pretest_lock.yaml freeze exact E1/E2/E3 definitions, contrasts,
uncertainty, fees/caps/risk and hold rules. The lock remains **PENDING** until the
Stage 5 preflight verifies actual funding settlement timestamps/rates (or actual
timestamp-only exclusions) and validates the E1 implementation on development
data before any test opening. E1's month-specific as-of artifacts must then be
generated before scoring each month, using only that month's permitted past.
Later E1 windows can contain previously elapsed test history; they are not
required to exist before January opens. No unverified
eight-hour settlement schedule or funding zero is assumed. These holds block test
opening, not completion of the authorized development policy work. G4 research
OOS gate is not passed. No user decision is needed to close this Stage 4 scope.

Public-flow conditional-response coefficients remain observational. Execution
impact, temporary liquidity, fees and spread are scenario assumptions. Matched
schedule correctness is no evidence of causal market savings; the long selected
decay and estimation/causal uncertainties persist. No new data/dependencies were
needed. Full resource/provenance details are in run manifests and session report.

```sh
.venv/bin/python -m pytest tests/test_stage04_policies.py -q
.venv/bin/python scripts/stage04.py all
```

**Stop at Stage 4. Final-test outcomes unopened; no historical implementation-shortfall backtest.**
"""
    (root/"reports/research/stage04_episode_policies.md").write_text(text)


def lock(root):
    root=Path(root);out,_=paths(root);docs=root/"docs";docs.mkdir(exist_ok=True)
    candidates=pd.read_csv(root/"reports/research/stage02_artifacts/candidate_selection.csv")
    candidates=candidates[(candidates.model=="B")&(candidates.taus_minutes=="5;30")].copy()
    if len(candidates)!=6:raise ValueError("Missing pre-existing fixed E1 family development selection")
    eligible=candidates[candidates.validation_mse_pooled<=candidates.validation_mse_pooled.min()*1.001]
    selected=eligible.sort_values("ridge",ascending=False).iloc[0]
    candidates.to_csv(out/"E1_development_regularization_selection.csv",index=False)
    doc="""# Stage 5 pretest policy/evaluator lock v1

Status: **PRETEST_LOCK_PENDING**. This is the Stage 4 protocol freeze, not
authorization to open outcomes or a completed G4 result. No 2026 observations
were opened. Machine-readable definitions/bindings are in
../configs/stage05_pretest_lock.yaml; its exact file SHA-256 is beside it.

The primary sample is Binance futures/um perpetual BTCUSDT, ETHUSDT, 2026-01-01
through 2026-06-30 UTC. Calendar labels only. Arrivals00/06/12/18;60×1min; completed
bar open t0−1min available exactly t0. Freeze all inputs before any future-bar
value access. Missing/invalid paired historical inputs exclude the whole episode;
jump/stale/verified zeros are retained. Only structural missing/invalid future
evaluation-bar QC may exclude an otherwise generated episode, common to all
policies; preserve all policy failures and adverse episodes. No realized values,
price movement, volatility or performance may select cases. No forward fill.

Forecasts/risk are Stage 4's trailing28d rules, positive1st-percentile floor,
240 typical fine-class observations/minimum120, ddof1 covariance and minimum40000
internal consecutive returns. X_i=.02sum Vhat_i;cap=.10Vhat;continuous reference
USDT units. Exact uniform exponential-cell Volterra impact, kappa=.001,theta=1,
5bp taker,1bp halfspread,m=0. Global beta uses common capped closest-uniform
reference and full covariance. T2 retains it with own variance decisions. Zero
risk fallback is theta0. No realized future volumes control constraints/sizes.

Monthly optimizer refit uses exactly365 full UTC days [month−365d,month), with
fixed selected tau60/ridge1, separate A/B, own L. Last target bar opens month−1min
and is available at month start. Lag context may precede the target window;
normalizers/L/targets do not use the evaluated month. Frozen June-2025 models
are a separately labeled sensitivity, never chosen based on test performance.
T0 projection,T1 forecast VWAP,T2 independent A,T3 joint A/full risk,T4 joint B/full
risk remain primary;T3B diagonal of B is secondary. T4−T3 compares estimated
families;T4−T3B isolates only cross impact. Both contrasts are precommitted.

Stage 5 scoring contract (NOT executed here): P0 is last completed close and
P_k primary is close of bar[t0+kmin,t0+(k+1)min). C_path=sum z(1−P_k/P0);
open and OHLC arithmetic-mean price proxies are separate timing sensitivities.
C_E=C_path+C_G(exact cells)+kappa_E sum z²/Vhat+1e-4(fee+spread)sum z+funding.
Report USDT and1e4C_E/W bps. Keep raw/full covariance risk and beta-weighted
preference separate from cash shortfall. Forecast denominators are primary;
realized volume may enter only an explicitly ex-post evaluator/participation
diagnostic. These are recorded unaffected path proxies plus assumed hypothetical
impact, never historical fills or causal own-trade response.

E0 uses optimizer B/common assumptions, circular/in-model diagnostic only.
E1 is a SEPARATE full PSD fixed(5,30)minute family, fit on exactly180 complete
days [month−210d,month−30d); its last label completes at month−30d. Same fixed
nuisance/normalization/penalty method, own L, no copying optimizer matrices.
Regularization is chosen only within the fixed(5,30)family using pre-existing
Stage 2 training/validation candidate losses and 0.1% tie/stronger-ridge rule
(selection table bound below). This is alternative past-data parameterization,
not independent randomized causal evidence. Require all180 calendar days and
QC/masks; if unavailable, use fixed June-end B solely as explicitly QUALIFIED
fallback, disclose it and never silently substitute rolling T4 parameters.
E2 sets each E1 component's off-diagonal to zero, retaining self/tau/L/temp.
E3 is one-factor-at-a-time about E1: entire-component amplitude0.5/1/2 applied
to all components together; decay multipliers0.5/2; kappa .0005/.001/.005;
cross interpolation(1−rho)diag(C)+rho C,rho0/.5/1. Baseline duplicates deduplicated.
Opposite-sign counterfactual uses D C D,D=diag(1,−1), PSD-certified, all components;
report as additional adverse world. No post-test grid expansion or favorable
scenario selection. No amplitude multiplication of isolated off-diagonal terms.
E4 remains absent/optional and requires separately authorized same-venue data.

H1: six monthly paired standardized conditional-response MSE A/B, practical0.5%
fit gain; show per asset,N0,negative months, contemporaneous descriptive label,
lag-only predictive distinction. H2 primary Delta_E=1e4(C_E(T3)−C_E(T4))/W;
secondary substitute T3B. Practical E1 target0.1bp; E2/E3 adverse losses retained,
underperformance fractions and maximum regret reported. No automatic favorable
hypothesis verdict. Daily paired losses and four within-day episodes clustered;
seven-contiguous-day moving-block bootstrap,500 draws,seed20261027,95% percentile
intervals for mean paired bps and relative cost change. Sample overlapping full
7day blocks with replacement until calendar length reached, truncate last block;
retain missing/excluded day labels, aggregate eligible paired episodes by day,
carry paired observations/all policies/evaluators together. Calendar-month,
weekday/weekend and past28d liquidity/volatility terciles; freeze tercile cutoffs
from July–December2025 episode inputs before test. Negative costs/denominator
near-zero relative ratios must be explicitly reported, not converted to wins.
Calibration uncertainty is separate from paired episode bootstrap.

Bounded sensitivities: one-factor-at-a-time theta0/1/2;inventory .005/.01/.02/.05;
cap .05/.10/.20; kappa .0005/.001/.005; price proxies above. Skip truly infeasible
capacity with common failure accounting. Secondary horizons30/120 recompute
forecasts/initial size, plus a fixed-notional comparison;fee2/5/10 and spread0/1/2
are assumptions and equal-notional fee constants cancel. C/D/SOL/L4 not authorized.

HOLD before opening ANY 2026 canonical outcomes: Stage 5 must acquire/verify
actual historical funding settlement timestamps/rates and specify continuous
inventory-weighted position exposure at each recorded settlement, OR verify
actual settlement timestamps and apply common fixed timestamp-only exclusion
for intervals containing settlements, including arrival exposure. No invented
8hour schedule, unverified zero cashflow, or rate-sign-based exclusions. Validate
and freeze the E1 estimator implementation/window/L/PSD on development data
before any test opening; then create each month's strict-as-of fit artifact
from available past data BEFORE scoring that month. Later-month E1 windows can
contain elapsed 2026 history, so all six artifacts are not a January prerequisite.
These are pending data/
implementation preflights, not discretion to retune the frozen protocol.

Future changes require dated reason, pre/post-outcome state, new version/hashes
and preservation of v1. Outcome-motivated scientific changes are exploratory or
require a fresh untouched test period. No final-test access is authorized here.
"""
    docpath=docs/"stage05_pretest_policy_evaluator_lock_v1.md";docpath.write_text(doc)
    epi=pd.read_csv(out/"episode_registry.csv")
    liquidity=epi.btc_initial_usdt+epi.eth_initial_usdt
    vol=np.sqrt(epi.cov00+2*epi.cov01+epi.cov11)
    thresholds=dict(liquidity_initial_portfolio_usdt=np.quantile(liquidity,[1/3,2/3]).tolist(),
                    volatility_equal_log_return_sum_std_per_minute=np.quantile(vol,[1/3,2/3]).tolist())
    # Hash a stable finite set, excluding self/run timestamp cycles.
    sourcefiles=list((root/"src/cryptocrossimpact").rglob("*.py"))+[root/"scripts/stage04.py",root/"tests/test_stage04_policies.py"]
    bind=[root/"CryptoCrossImpact_Research_Specification_v1_2026-10-27.md",root/"SPEC_CHANGELOG.md",root/"configs/stage04_policies.yaml",
          root/"data/registry/source_manifest.json",root/"reports/research/stage02_artifacts/pretest_estimation_lock.json",docpath,
          out/"monthly_coverage.csv",out/"policy_fairness.csv",out/"model_registry.csv",out/"E1_development_regularization_selection.csv",out/"test_results.json"]
    bind+=list(out.glob("model_*.json"))
    payload=dict(version="stage05-pretest-lock-v1",status="PRETEST_LOCK_PENDING",test_outcomes_unopened=True,stage5_started=False,
        sample=dict(venue="Binance",market="futures/um",symbols=["BTCUSDT","ETHUSDT"],start="2026-01-01",end="2026-06-30",arrivals_UTC=[0,6,12,18]),
        primary_policy_config="configs/stage04_policies.yaml",protocol_document=str(docpath.relative_to(root)),
        policies=["T0","T1","T2","T3","T4"],secondary_policy="T3B",optimizer_refit=dict(days=365,taus_minutes=[60],ridge=1),
        E1=dict(days=180,gap_days=30,end_exclusive="month_start minus 30 days",taus_minutes=[5,30],ridge=float(selected.ridge),
                selection="Existing fixed-(5,30) Stage 2 train/validation losses; within0.1% prefer stronger ridge",
                fallback="Fixed June-end development B, QUALIFIED only if full E1 historical block unavailable"),
        E2="diagonal each E1 component; otherwise identical",
        E3=dict(combination="one_factor_at_a_time_around_E1_deduplicate_baseline",entire_matrix_amplitude=[.5,1,2],decay_multiplier=[.5,2],
                kappa=[.0005,.001,.005],cross_rho=[0,.5,1],opposite_sign="D C D, D=diag(1,-1), PSD certified"),
        inference=dict(block_calendar_days=7,replicates=500,seed=20261027,interval="95% percentile",paired_unit="UTC calendar day"),
        development_regime_tercile_thresholds=thresholds,
        holds=["Verify actual funding settlement timestamps/rates or actual timestamp-only common exclusions before test opening",
               "Validate/freeze E1 implementation on development before test opening; then generate strict-as-of E1 artifacts before each monthly scoring, no retuning"],
        bindings={str(p.relative_to(root)):sha256(p) for p in bind+sourcefiles})
    path=root/"configs/stage05_pretest_lock.yaml";path.write_text(yaml.safe_dump(payload,sort_keys=False))
    digest=sha256(path);(root/"configs/stage05_pretest_lock.sha256").write_text(f"{digest}  stage05_pretest_lock.yaml\n")
    save(out/"pretest_lock_status.json",dict(status=payload["status"],sha256=digest,path=str(path.relative_to(root)),holds=payload["holds"],test_outcomes_unopened=True))
    report_path=root/"reports/research/stage04_episode_policies.md"
    if report_path.exists():
        marker="\n<!-- pretest-lock-sha -->"
        report_path.write_text(report_path.read_text().split(marker)[0]+marker+f"\nPretest lock v1 SHA-256: `{digest}`. Status: **PRETEST_LOCK_PENDING**.\n")
