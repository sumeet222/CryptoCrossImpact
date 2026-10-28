"""Cash-consistent, exact exponential cell integrals; no market-data I/O."""
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import eigvalsh

from ..data.storage import sha256
from ..kernel.fit import level_kernel, validate_components

ASSETS = ("BTCUSDT", "ETHUSDT")
UNITS = "C maps q/sqrt(L) to 1e4*sqrt(L)*log_return; tau in minutes"
EXPECTED_SCHEMA = {
    "asset_order", "component_diagnostics", "constraint_or_normal_equation_residual",
    "diagnostic_only", "execution_kernel_export_allowed", "finite_grid_check", "indices",
    "liquidity_usdt", "matrices", "memory_minutes", "model", "normalization", "objective",
    "provenance", "return_basis", "ridge", "solver", "standardized_design_condition",
    "standardized_training_mse", "status", "taus_minutes", "theta_standardized",
    "training_end_exclusive", "training_rows", "training_start", "units",
    "validation_end_exclusive", "validation_mse", "validation_mse_pooled", "validation_start"
}


def psd_diagnostics(matrix, relative_tolerance=1e-9):
    """Tolerance scales with the actual matrix norm, even for tiny cash Hessians.

    Never use max(1,norm) for a USDT/notional^2 matrix: that would hide
    economically indefinite matrices whose entries are naturally around 1e-12.
    No eigenvalue projection or diagonal regularization is performed.
    """
    a = np.asarray(matrix, dtype=float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not np.isfinite(a).all():
        raise ValueError("Expected finite square matrix")
    scale = max(float(np.max(np.abs(a))), np.finfo(float).tiny)
    if np.max(np.abs(a-a.T)) > relative_tolerance*scale:
        raise ValueError("Matrix is not symmetric")
    eigen = eigvalsh(a, check_finite=False)
    norm = max(float(np.max(np.abs(eigen))), np.finfo(float).tiny)
    if eigen[0] < -relative_tolerance*norm:
        raise ValueError("Materially indefinite matrix; no PSD repair permitted")
    return dict(min_eigenvalue=float(eigen[0]), max_eigenvalue=float(eigen[-1]),
                relative_min_eigenvalue=float(eigen[0]/norm),
                condition_number=float(eigen[-1]/eigen[0]) if eigen[0] > relative_tolerance*norm else None,
                relative_tolerance=relative_tolerance)


@dataclass(frozen=True)
class Kernel:
    """C in economic f→y coordinates, tau in minutes, L in USDT.

    One/two-asset synthetic limits are allowed; verified Stage 2 imports require
    the fixed two-asset contract. Arrays are defensive copies marked read-only.
    """
    assets: tuple
    matrices: np.ndarray
    taus_minutes: np.ndarray
    liquidity_usdt: np.ndarray
    label: str = "synthetic"
    source_sha256: str | None = None

    def __post_init__(self):
        assets = tuple(self.assets)
        c = np.array(self.matrices, dtype=float, copy=True)
        tau = np.array(self.taus_minutes, dtype=float, copy=True)
        l = np.array(self.liquidity_usdt, dtype=float, copy=True)
        if len(assets) not in (1,2) or len(set(assets)) != len(assets) or not set(assets).issubset(ASSETS):
            raise ValueError("Unverified asset identity")
        if tau.ndim!=1 or c.ndim!=3 or c.shape != (len(tau), len(assets), len(assets)) or not len(tau):
            raise ValueError("Kernel component shape mismatch")
        if l.shape != (len(assets),) or not np.isfinite(l).all() or np.any(l <= 0):
            raise ValueError("Positive finite USDT liquidity units required")
        if not np.isfinite(tau).all() or np.any(tau <= 0):
            raise ValueError("Positive finite minute time constants required")
        for component in c: psd_diagnostics(component)
        for array in (c,tau,l): array.setflags(write=False)
        object.__setattr__(self,"assets",assets)
        object.__setattr__(self,"matrices",c)
        object.__setattr__(self,"taus_minutes",tau)
        object.__setattr__(self,"liquidity_usdt",l)

    def level(self, lags_minutes):
        lags = np.asarray(lags_minutes,dtype=float)
        if not np.isfinite(lags).all() or (lags < 0).any():
            raise ValueError("Nonnegative finite minute lags required")
        return np.einsum("lk,kij->lij",np.exp(-lags[:,None]/self.taus_minutes),self.matrices)


def load_stage02(root, model_name, path=None):
    """Strict known Stage 2 implicit schema + frozen hash; never opens Parquet.

    Stage 2 did not serialize an explicit schema version. Identify its complete
    validated key set as stage02-kernel-implicit-v1; reject unknown revisions.
    """
    if model_name not in ("A","B"):
        raise ValueError("Diagnostic U/N0 is not an executable kernel")
    root=Path(root);folder=root/"reports/research/stage02_artifacts"
    path=Path(path) if path is not None else folder/f"model_{model_name}.json"
    if path.resolve()!=(folder/f"model_{model_name}.json").resolve():
        raise ValueError("Stage 3 firewall: only frozen model JSON paths allowed; no outcome inputs")
    lock=json.loads((folder/"pretest_estimation_lock.json").read_text())
    if sha256(path) != lock["model_sha256"][model_name]:
        raise ValueError("Stage 2 model hash differs from estimation lock")
    model=json.loads(path.read_text())
    manifest_path=root/"data/registry/source_manifest.json"
    manifest=json.loads(manifest_path.read_text())
    if sha256(manifest_path)!=model["provenance"]["source_manifest_sha256"]:
        raise ValueError("Unverified source-manifest revision")
    if (manifest["venue"],manifest["market"],manifest["interval"],manifest["price_type"]) != ("Binance","futures/um","1m","last traded price"):
        raise ValueError("Unverified market/price identity")
    return adapt_stage02(model,sha256(path),model_name)


def adapt_stage02(model, source_sha256=None, expected_model=None):
    if set(model) != EXPECTED_SCHEMA:
        raise ValueError("Unidentified Stage 2 model schema revision")
    if model["model"] not in ("A","B") or (expected_model and model["model"] != expected_model):
        raise ValueError("Diagnostic or wrong model identity")
    if tuple(model["asset_order"]) != ASSETS:
        raise ValueError("Unverified Stage 2 asset order")
    if model["status"] != "optimal" or model["diagnostic_only"] or model["execution_kernel_export_allowed"] is not True:
        raise ValueError("Unverified or nonexportable model")
    if model["units"] != UNITS or model["return_basis"] != "G(0) current; G(l)-G(l-1) lags 1..H; no H+1 tail term":
        raise ValueError("Wrong kernel units or level/return convention")
    provenance=model["provenance"]
    if provenance.get("market","futures/um")!="futures/um":
        raise ValueError("Unverified market identity")
    if provenance["stage"] != "G2 development only" or provenance["final_outcome_scoring_performed"]:
        raise ValueError("Model provenance violates Stage 3 firewall")
    if (pd.Timestamp(model["training_end_exclusive"],tz="UTC") > pd.Timestamp("2026-01-01",tz="UTC") or
        pd.Timestamp(model["validation_end_exclusive"],tz="UTC") > pd.Timestamp("2026-01-01",tz="UTC") or
        pd.Timestamp(provenance["data_latest_open_utc"]) >= pd.Timestamp("2026-01-01",tz="UTC")):
        raise ValueError("Model uses 2026 outcomes")
    identities=provenance["development_partition_ids"]
    if not identities or any(k.split("/")[0] not in ASSETS or k.split("/")[-1] >= "2026-01" for k in identities):
        raise ValueError("Unverified market/history identity")
    # Reuse the Stage 2 validator/export API, with an additional tiny-scale check.
    validate_components(model["matrices"])
    kernel=Kernel(ASSETS,model["matrices"],model["taus_minutes"],model["liquidity_usdt"],model["model"],source_sha256)
    if model["model"] == "A" and np.any(kernel.matrices[:,0,1] != 0):
        raise ValueError("Diagonal model A contains cross-impact")
    np.testing.assert_allclose(kernel.level([0,1,60,120]),level_kernel(model,[0,1,60,120]),rtol=1e-14,atol=0)
    return kernel


def exponential_factors(n, delta_minutes, tau_minutes, convention="exact_exponential_cells"):
    """Uniform-bin factors for total notional, not rates; no extra delta factor.

    a0 = (x + expm1(-x))/x^2, am = exp(-(m-1)x)*(expm1(-x)/x)^2.
    a0 integrates the causal SAME-CELL TRIANGLE ONCE. x=d/tau.
    """
    if not isinstance(n,(int,np.integer)) or n < 1 or not np.isfinite([delta_minutes,tau_minutes]).all() or min(delta_minutes,tau_minutes)<=0:
        raise ValueError("Positive grid size and minute durations required")
    x=delta_minutes/tau_minutes
    if convention == "half_cell_sampled":
        result=np.exp(-np.arange(n)*x);result[0]=.5
        return result
    if convention != "exact_exponential_cells":
        raise ValueError("Unknown impact cell convention")
    result=np.empty(n)
    result[0]=(.5-x/6+x*x/24-x**3/120+x**4/720) if x<1e-3 else (x+np.expm1(-x))/(x*x)
    result[1:]=np.exp(-np.arange(n-1)*x)*(np.expm1(-x)/x)**2
    return result


def cash_hessian(kernel,n,delta_minutes=1.,convention="exact_exponential_cells"):
    """H with cash = .5 z.T H z, z time-major TOTAL sold USDT per bin.

    For uniform rate w_k/d, exact cell integration yields
    cash=1e-4 sum_{k>=j} w_k.T [sum C_a a_(k-j)] w_j.
    Let T be that lower time-block matrix in raw USDT coordinates. H=T+T.T:
    diagonal blocks double the triangular a0; off-time blocks appear only once.
    H=60 in calibration never truncates the fitted exponential level here.
    """
    size=len(kernel.assets);distance=np.abs(np.arange(n)[:,None]-np.arange(n)[None,:])
    h=np.zeros((n*size,n*size));unit=1/np.sqrt(kernel.liquidity_usdt)
    for c,tau in zip(kernel.matrices,kernel.taus_minutes):
        a=exponential_factors(n,delta_minutes,float(tau),convention)
        temporal=a[distance];np.fill_diagonal(temporal,2*a[0])
        h += 1e-4*np.kron(temporal,c*unit[:,None]*unit[None,:])
    return h,psd_diagnostics(h)


def triangular_cash(kernel,schedule,delta_minutes=1.,convention="exact_exponential_cells"):
    """Independent lower-time-block evaluation, including arbitrary signed trades."""
    z=np.asarray(schedule,dtype=float)
    if z.ndim != 2 or z.shape[1]!=len(kernel.assets) or not np.isfinite(z).all():
        raise ValueError("Schedule shape/finite check failed")
    w=z/np.sqrt(kernel.liquidity_usdt);cost=0.
    for c,tau in zip(kernel.matrices,kernel.taus_minutes):
        a=exponential_factors(len(z),delta_minutes,float(tau),convention)
        for k in range(len(z)):
            for j in range(k+1):cost += 1e-4*a[k-j]*(w[k]@c@w[j])
    return float(cost)
