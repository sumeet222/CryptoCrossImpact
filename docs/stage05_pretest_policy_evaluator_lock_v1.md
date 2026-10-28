# Stage 5 pretest policy/evaluator lock v1

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
