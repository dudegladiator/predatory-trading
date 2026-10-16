"""Week 8 (extension C): endogenous distress and contagion, Section III.B.

Survival hurdle (eq. 21). Trader i expects I_d traders to fail, itself
included: I_d - 1 others liquidate and the rest prey with the vigour of the
I_d-distressed equilibrium. W(I_d) is the highest wealth at t0 at which i
cannot avoid falling to the threshold W_low whatever it does:

    W(I_d) = W_low + D(I_d),   D(I_d) = -max over a_i of min over t of ΔW_i(t).

On our grid the wealth change over step k is exactly
    λ [ (x_{k+1}^2 - x_k^2) / 2 + x̄_k ΔX₋ᵢ,k ],   x̄_k = (x_k + x_{k+1}) / 2,
so ΔW_i(t) = λ [ (x_t^2 - x0^2) / 2 + L_t ], with L_t linear in the path. The
x^2 term makes the max-min non-convex, so it is solved by sequential linear
programming: replace x^2/2 by its tangent (never above it, so every LP answer
is truly achievable), solve, re-linearize at the new path, repeat. Each step can
only improve; several starting paths guard against local optima.

By default i may use any strategy, as eq. (21) says, including buying to push
up the price and with it the paper value of its own holdings.
can_buy=False restricts i to selling or holding, for comparison.
"""

from dataclasses import replace

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, vstack

from closed_form import equilibrium_rates, liquidation_end
from model import Params, schedule, speed_caps


def others_when(p: Params) -> np.ndarray:
    """Rates of everyone except trader i (in a distressed slot) when I_d fail."""
    if p.I_d == p.I:  # nobody left to prey: everyone else liquidates
        return np.tile(schedule(p, [(liquidation_end(p), -p.A / p.I)]), (p.I - 1, 1))
    return equilibrium_rates(p)[1:]


def _others_holdings(p: Params, others: np.ndarray) -> np.ndarray:
    return p.x0 * (p.I - 1) + np.concatenate([[0.0], np.cumsum(others.sum(axis=0) * p.dt)])


def wealth_change(p: Params, others: np.ndarray, x: np.ndarray) -> np.ndarray:
    """ΔW_i(t) on the grid for trader i's holdings path x (N + 1,)."""
    dX = np.diff(_others_holdings(p, others))
    L = np.concatenate([[0.0], np.cumsum((x[:-1] + x[1:]) / 2 * dX)])
    return p.lam * ((x**2 - p.x0**2) / 2 + L)


def _caps(p: Params, others: np.ndarray, can_buy: bool) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = speed_caps(others, p.A)
    return lo, hi if can_buy else np.minimum(hi, 0.0)


def _path_at_cap(p: Params, rate: np.ndarray, stop: float) -> np.ndarray:
    """Holdings trading at `rate` (per step) from x0 until reaching `stop`."""
    x = [p.x0]
    for r in rate * p.dt:
        x.append(min(x[-1] + r, stop) if r > 0 else max(x[-1] + r, stop))
    return np.array(x)


def _sequential_lp(p: Params, others: np.ndarray, x: np.ndarray, can_buy: bool,
                   max_iter: int = 50) -> tuple[float, np.ndarray]:
    """Improve path x for max min_t ΔW_i(t). Returns (that max-min, path)."""
    n = others.shape[1]
    nx = n + 1
    iL, im = nx, 2 * nx                   # variables: x_0..x_N, L_0..L_N, m
    nvar = 2 * nx + 1
    dX = np.diff(_others_holdings(p, others))
    k = np.arange(n)
    # L_{k+1} - L_k - dX_k (x_k + x_{k+1}) / 2 = 0
    eq = csr_matrix((np.concatenate([np.ones(n), -np.ones(n), -dX / 2, -dX / 2]),
                     (np.tile(k, 4), np.concatenate([iL + k + 1, iL + k, k, k + 1]))),
                    shape=(n, nvar))
    # lo dt <= x_{k+1} - x_k <= hi dt
    lo, hi = _caps(p, others, can_buy)
    step = csr_matrix((np.concatenate([np.ones(n), -np.ones(n)]),
                       (np.tile(k, 2), np.concatenate([k + 1, k]))), shape=(n, nvar))
    bounds = ([(p.x0, p.x0)] + [(-p.x_bar, p.x_bar)] * n
              + [(0.0, 0.0)] + [(None, None)] * n + [(None, None)])
    c = np.zeros(nvar)
    c[im] = -1.0  # maximise m
    t = np.arange(nx)
    best = wealth_change(p, others, x).min()
    for _ in range(max_iter):
        # m <= λ [ y_t x_t - y_t^2 / 2 - x0^2 / 2 + L_t ]   (tangent of x^2/2 at y)
        tangent = csr_matrix((np.concatenate([np.ones(nx), -p.lam * x, -p.lam * np.ones(nx)]),
                              (np.tile(t, 3), np.concatenate([np.full(nx, im), t, iL + t]))),
                             shape=(nx, nvar))
        res = linprog(c, A_ub=vstack([step, -step, tangent]),
                      b_ub=np.concatenate([hi * p.dt, -lo * p.dt, -p.lam * (x**2 + p.x0**2) / 2]),
                      A_eq=eq, b_eq=np.zeros(n), bounds=bounds, method="highs")
        assert res.status == 0, res.message
        new = res.x[:nx]
        value = wealth_change(p, others, new).min()
        if value <= best + 1e-9:
            break
        x, best = new, value
    return best, x


def survival_drop(p: Params, can_buy: bool = True) -> tuple[float, np.ndarray]:
    """D(I_d) and trader i's best survival path, for p.I_d expected failures."""
    others = others_when(p)
    lo, hi = _caps(p, others, can_buy)
    starts = [np.full(others.shape[1] + 1, p.x0),      # hold
              _path_at_cap(p, lo, 0.0),                # sell out as fast as allowed
              _path_at_cap(p, lo, -p.x_bar)]           # sell and go short
    if can_buy:
        starts.append(_path_at_cap(p, hi, p.x_bar))    # buy as fast as allowed
    value, path = max((_sequential_lp(p, others, x, can_buy) for x in starts), key=lambda r: r[0])
    return -value, path


def hurdles(p: Params, can_buy: bool = True) -> np.ndarray:
    """D(I_d) for I_d = 0 .. I, with D(0) = 0. W(I_d) = W_low + D(I_d)."""
    return np.array([0.0] + [survival_drop(replace(p, I_d=k), can_buy)[0]
                             for k in range(1, p.I + 1)])


def equilibria(wealth: np.ndarray, W_low: float, D: np.ndarray) -> list[int]:
    """Numbers of failures I_d consistent with the wealth levels: exactly the
    I_d traders with wealth <= W(I_d) fail (Section III.B)."""
    return [k for k in range(len(wealth) + 1) if np.sum(wealth <= W_low + D[k]) == k]


def cascade(wealth: np.ndarray, W_low: float, D: np.ndarray) -> list[list[int]]:
    """The ripple: start from the traders forced out (wealth <= W_low); while
    more traders fall below the hurdle for the current number of failures, add
    them. Returns the failed traders after each step; the last is the smallest
    equilibrium at or above the forced failures."""
    failed = list(np.flatnonzero(wealth <= W_low))
    steps = [failed]
    while True:
        now = list(np.flatnonzero(wealth <= W_low + D[len(failed)]))
        if len(now) == len(failed):
            return steps
        failed = now
        steps.append(failed)
