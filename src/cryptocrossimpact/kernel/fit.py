"""Small sufficient-statistic ridge/SDP fits in cash-consistent coordinates."""
from dataclasses import dataclass

import cvxpy as cp
import numpy as np

from .features import feature_names


@dataclass
class Stats:
    n: int
    gram: np.ndarray
    xy: np.ndarray
    yy: np.ndarray

    @classmethod
    def zeros(cls, p):
        return cls(0, np.zeros((p,p)), np.zeros((p,2)), np.zeros(2))

    @classmethod
    def rows(cls, x, y):
        return cls(len(x), x.T @ x, x.T @ y, np.sum(y*y, axis=0))

    def add(self, other, weight=1):
        self.n += int(other.n * weight)
        self.gram += weight * other.gram
        self.xy += weight * other.xy
        self.yy += weight * other.yy
        return self

    def subset(self, indices):
        g = self.gram[np.ix_(indices, indices)] if self.gram.ndim == 2 else self.gram[:,indices][:,:,indices]
        return Stats(self.n, g, self.xy[indices], self.yy.copy())


def transforms(raw):
    if raw.n < 2:
        raise ValueError("Insufficient estimation rows")
    mean = raw.gram[0] / raw.n
    scale = np.sqrt(np.maximum(np.diag(raw.gram)/raw.n-mean**2, 0))
    mean[0], scale[0] = 0., 1.
    if (scale <= 1e-14).any():
        raise ValueError("Unidentified constant predictor; diagnose before fitting")
    ym = raw.xy[0] / raw.n
    ys = np.sqrt(raw.yy/raw.n - ym**2)
    if (ys <= 0).any():
        raise ValueError("Degenerate target")
    return dict(mean=mean.tolist(), scale=scale.tolist(), target_scale=ys.tolist())


def normalize(raw, normal):
    mean, scale = np.array(normal["mean"]), np.array(normal["scale"])
    ys = np.array(normal["target_scale"])
    t = np.diag(1/scale)
    t[0,1:] = -mean[1:]/scale[1:]
    return Stats(raw.n, t.T @ raw.gram @ t, (t.T @ raw.xy)/ys, raw.yy/ys**2)


def normalized_rows(x, normal):
    return (x-np.array(normal["mean"])) / np.array(normal["scale"])


def columns(taus, all_taus, model):
    base = 1 + len(feature_names())
    indices = list(range(base))
    if model != "N0":
        for tau in taus:
            at = all_taus.index(tau)
            indices.extend([base+2*at, base+2*at+1])
    return indices


def loss(stats, theta):
    values = []
    for i in range(2):
        g = stats.gram if stats.gram.ndim == 2 else stats.gram[i]
        values.append(float((theta[:,i] @ g @ theta[:,i] - 2*theta[:,i] @ stats.xy[:,i] + stats.yy[i])/stats.n))
    return np.array(values)


def validate_components(matrices, relative_tolerance=1e-8):
    diagnostics = []
    for matrix in np.asarray(matrices):
        scale = max(1., float(np.linalg.norm(matrix, 2)))
        if not np.isfinite(matrix).all() or np.max(np.abs(matrix-matrix.T)) > relative_tolerance*scale:
            raise ValueError("Nonsymmetric/nonfinite economic kernel")
        eigen = np.linalg.eigvalsh(matrix)
        if eigen.min() < -relative_tolerance*scale:
            raise ValueError("Materially indefinite kernel; no silent PSD repair")
        denom = np.sqrt(max(0., matrix[0,0]*matrix[1,1]))
        diagnostics.append(dict(eigenvalues=eigen.tolist(), relative_min_eigenvalue=float(eigen.min()/scale),
            psd_binding=bool(eigen.min() <= 1e-6*scale),
            cross_ratio=float(matrix[0,1]/denom) if denom > 1e-12*scale else None,
            condition_number=float(eigen.max()/eigen.min()) if eigen.min()>1e-12*scale else None))
    return diagnostics


def estimate(stats, normal, taus, all_taus, model, ridge, solver="CLARABEL", force_diagonal=False, omit_return_controls=False):
    """Joint mean standardized loss + lambda mean squared nonintercept effects.

    beta_ij = C_ij * s(flow_basis_j) / s(y_i). CVXPY restricts C in
    its original economic units; whitening never imposes symmetry on beta.
    Intercepts are free. N0/U have analytic unconstrained ridge solutions.
    """
    indices = columns(list(taus), list(all_taus), model)
    sample = stats.subset(indices)
    p, n = len(indices), sample.n
    nc = 1 + len(feature_names())
    scale = np.array(normal["scale"])[indices]
    ys = np.array(normal["target_scale"])
    matrices, constraints, residual = [], [], 0.
    if model in ("N0", "U"):
        coefficients = []
        for i in range(2):
            g = sample.gram if sample.gram.ndim == 2 else sample.gram[i]
            penalty = np.eye(p)*ridge; penalty[0,0]=0
            system = g/n + penalty
            solution = np.linalg.lstsq(system, sample.xy[:,i]/n, rcond=1e-12)[0]
            residual = max(residual, float(np.linalg.norm(system@solution-sample.xy[:,i]/n)))
            coefficients.append(solution)
        theta = np.column_stack(coefficients)
        if model == "U":
            for k in range(len(taus)):
                matrices.append(theta[nc+2*k:nc+2*k+2].T*ys[:,None]/scale[nc+2*k:nc+2*k+2][None,:])
        status, used_solver, objective_value = "optimal", "analytic_lstsq", float(loss(sample, theta).mean()+ridge*np.sum(theta[1:]**2)/2)
    else:
        controls = cp.Variable((nc,2))
        if omit_return_controls:
            return_rows=[1+i for i,name in enumerate(feature_names()) if name.startswith("return_")]
            constraints.append(controls[return_rows,:] == 0)
        cref = float(np.median(ys[:,None]/scale[nc:][None,:]))
        cvars = []
        for k in range(len(taus)):
            if model == "A" or force_diagonal:
                diag = cp.Variable(2, nonneg=True)
                c = cp.diag(diag)
            else:
                c = cp.Variable((2,2), symmetric=True)
                constraints.append(c >> 0)
            cvars.append(c)
        blocks = [controls]
        for k, c in enumerate(cvars):
            # Rows = input assets, columns = response assets, units restored here.
            multiplier = cref*scale[nc+2*k:nc+2*k+2,None]/ys[None,:]
            blocks.append(cp.multiply(c.T, multiplier))
        beta = cp.vstack(blocks)
        objective = 0
        for i in range(2):
            g = sample.gram if sample.gram.ndim == 2 else sample.gram[i]
            g = (g+g.T)/(2*n)
            if np.linalg.eigvalsh(g).min() < -1e-10*max(1., np.linalg.norm(g,2)):
                raise ValueError("Sufficient-statistic Gram is materially indefinite")
            objective += .5*(cp.quad_form(beta[:,i], cp.psd_wrap(g))-2*(sample.xy[:,i]/n)@beta[:,i]+sample.yy[i]/n)
        objective += .5*ridge*cp.sum_squares(beta[1:])
        problem = cp.Problem(cp.Minimize(objective), constraints)
        kwargs = dict(tol_gap_abs=1e-9, tol_gap_rel=1e-8, tol_feas=1e-9, max_iter=250) if solver == "CLARABEL" else dict(eps=1e-7,max_iters=20000)
        problem.solve(solver=solver, **kwargs)
        if problem.status != "optimal" or beta.value is None:
            raise ValueError(f"Nonconverged {solver} estimator: {problem.status}")
        theta = beta.value
        matrices = [c.value*cref for c in cvars]
        residual = max([float(np.max(c.violation())) for c in constraints] or [0.])
        status, used_solver, objective_value = problem.status, solver, float(problem.value)
    if not np.isfinite(theta).all() or residual > 1e-6:
        raise ValueError("Estimator failed finite/constraint residual check")
    eigen = validate_components(matrices) if model in ("A","B") else []
    if model == "N0":
        matrices = []
    return dict(model=model, taus_minutes=list(taus) if model!="N0" else [], ridge=float(ridge),
        matrices=np.array(matrices).tolist(), theta_standardized=theta.tolist(), indices=indices,
        normalization=normal, status=status, solver=used_solver, objective=objective_value,
        constraint_or_normal_equation_residual=residual, component_diagnostics=eigen,
        standardized_training_mse=loss(sample,theta).tolist(), training_rows=n,
        diagnostic_only=model in ("N0","U"), execution_kernel_export_allowed=model in ("A","B"),
        units="C maps q/sqrt(L) to 1e4*sqrt(L)*log_return; tau in minutes",
        standardized_design_condition=float(np.linalg.cond(sample.gram if sample.gram.ndim==2 else sample.gram[0])))


def predict(model, raw_design):
    x = normalized_rows(raw_design, model["normalization"])[:,model["indices"]]
    return (x @ np.array(model["theta_standardized"]))*np.array(model["normalization"]["target_scale"])


def level_kernel(model, lags):
    if not model.get("execution_kernel_export_allowed") or model["model"] not in ("A","B"):
        raise ValueError("Diagnostic U/N0 cannot be exported as an admissible execution kernel")
    validate_components(model["matrices"])
    return np.einsum("lk,kij->lij",np.exp(-np.asarray(lags)[:,None]/np.array(model["taus_minutes"])[None,:]), np.array(model["matrices"]))


def finite_grid_check(model, seed=20261027, n=32):
    """Model-validity diagnostic only: point-lag kernel, half same-cell cost.

    S_{ka,lb}=G_ab(|k-l|)/2 and cash=1e-4*w.T*S*w. Stage 3 must
    separately validate its cell-integrated production discretization.
    """
    lag = np.abs(np.arange(n)[:,None]-np.arange(n)[None,:])
    g = level_kernel(model,np.arange(n))
    s = .5*g[lag].transpose(0,2,1,3).reshape(2*n,2*n)
    eig = np.linalg.eigvalsh(s)
    rng = np.random.default_rng(seed)
    u = rng.normal(size=(100,n,2));u -= u.mean(axis=1,keepdims=True)
    costs = 1e-4*np.einsum("bi,ij,bj->b",u.reshape(100,-1),s,u.reshape(100,-1))
    if eig.min() < -1e-8*max(1.,np.linalg.norm(s,2)) or costs.min() < -1e-10:
        raise ValueError("Finite-grid nonnegative cost check failed")
    return dict(grid_minutes=n, same_cell="half", min_eigenvalue=float(eig.min()), min_round_trip_cash_cost=float(costs.min()), checks=100)
