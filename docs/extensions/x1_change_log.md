# X1 interpretation and change record — 2026-10-28 UTC

Status: explicitly authorized X1.0, exploratory after original Stage5 inspection.
Original research specification, SPEC_CHANGELOG and Stage1–5 artifacts unchanged.
No new 2026 outcomes, including July–September, opened by this extension.

- **New scope:** replace constant intrahour assumptions and static execution only
  inside X1. Original historical study and H1/H2 remain unchanged. Source is the
  authorized Session1 prompt, not a successor core specification.
- **Predeclared choices:** D0/D1=T3B (B self coefficients, tau, L); complete UTC
  days for profiles, median positive within-hour reference, n/(n+50) shrinkage;
  tau15 activity with no grid; 5min cadence; original fixed caps/covariance/beta.
  Exact treatment of incomplete/zero hours is in protocol v1.
- **Scenario control clarification:** P4M, median-only adaptive temporary cost,
  accompanies P4 to distinguish .25/.5/.25 inverse-volume weighting from median
  recalibration. This implements the prompt's required matched point control.
  P4 versus P2/P3 remains the combined scenario/recalibration contrast.
- **Implementation:** direct OSQP solves the original scaled convex problem with
  original eps1e-9/polishing and explicit KKT/decomposition checks; it avoids
  repeated symbolic CVXPY construction for twelve updates. Independent old
  OSQP/CLARABEL parity and unchanged-tail tests pass. No scientific objective,
  cap or solver tolerance was relaxed.
- **Forecast-only gate, before X1 economic comparison:** V2 failed the declared
  RMSLE evidence gate, retained as a negative forecast result; P3 NOT_RUN.
  Training-calibrated V1 bands passed the declared 5-percentage-point maximum
  coverage-error gate; P4/P4M use V1. No activity/profile retuning after this gate.
- **Preservation:** original global changelog/README/index were not appended
  because their old lock bindings and all prior artifacts must remain intact.
  This file, X1 protocol, X1 report and extension experiment index provide the
  new study's dated lineage and reproduction commands.

No robust/minimax kernel control, random Volterra model, alpha, nonlinear
impact, updated-cap experiment, new market or new data dependency was added.

## Output-only zero-volume recovery, after development replay began

The original Stage5 scorer represents positive sales into observed zero turnover
with an infinite maximum participation. JSON with allow_nan=False correctly
rejected that infinity for 2025-08-29 06:00. The existing committed schedule was
preserved; the episode was not scientifically excluded. X1 now serializes this
specific nonfinite maximum as null plus
INFEASIBLE_POSITIVE_SALE_ZERO_VOLUME. All cash amounts and finite ratios remain
identical; separate zero-volume/sales counts retain infeasibility.

Original numerical lock/source bytes are preserved under X1 provenance. The v2
lock links its predecessor. AST comparison confirms unchanged existing forecasting,
policy construction and development algorithms; only lock metadata and the new
serialization wrapper differ. A dedicated regression checks that zero-volume
cash amounts stay identical and the explicit flag is JSON-safe. Original Stage5
source is unchanged. The initial serialization-failure record remains archived;
resume fills its missing score receipt from the unchanged schedule.
