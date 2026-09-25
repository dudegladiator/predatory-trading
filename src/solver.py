"""Numerical best responses: Lemma 1 turned into a linear program."""

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import diags, vstack

from model import Params, speed_caps


def _optimal_holdings(p: Params, others: np.ndarray, others_start: float,
                      start: float, target: float, limit: float) -> np.ndarray:
    """LP for one trader's optimal holdings path against fixed opponents."""
    n = others.shape[1]
    X = others_start + np.concatenate([[0.0], np.cumsum(others.sum(axis=0) * p.dt)])
    w = (X[:-1] + X[1:]) / 2
    c = np.concatenate([[0.0], w]) - np.concatenate([w, [0.0]])
    lo, hi = speed_caps(others, p.A)
    D = diags([-np.ones(n), np.ones(n)], [0, 1], shape=(n, n + 1))
    bounds = [(start, start)] + [(-limit, limit)] * (n - 1) + [(target, target)]
    res = linprog(c, A_ub=vstack([D, -D]), b_ub=np.concatenate([hi * p.dt, -lo * p.dt]),
                  bounds=bounds, method="highs")
    assert res.status == 0, res.message
    return res.x


def best_response(p: Params, rates: np.ndarray, i: int, target: float) -> np.ndarray:
    """Trader i's payoff-maximising rates with everyone else's held fixed."""
    start = np.full(p.I, p.x0)
    x = _optimal_holdings(p, np.delete(rates, i, axis=0), start.sum() - start[i],
                          start[i], target, p.x_bar)
    out = rates.copy()
    out[i] = np.diff(x) / p.dt
    return out
