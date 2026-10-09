"""Numerical best responses: Lemma 1 turned into a linear program."""

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import diags, vstack

from model import Params, schedule, simulate, speed_caps


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


def collusive_response(p: Params, rates: np.ndarray) -> np.ndarray:
    """Predators maximise their joint profit against fixed distressed traders."""
    x = _optimal_holdings(p, rates[: p.I_d], p.x0 * p.I_d,
                          p.x0 * p.I_p, p.x_bar * p.I_p, p.x_bar * p.I_p)
    out = rates.copy()
    out[p.I_d:] = np.diff(x) / p.dt / p.I_p
    return out


def naive_start(p: Params, distressed: np.ndarray) -> np.ndarray:
    """Starting point: predators buy steadily while distressed traders sell."""
    end = p.t0 + p.x0 / (p.A / p.I)
    predator = schedule(p, [(end, (p.x_bar - p.x0) / (end - p.t0))])
    return np.vstack([distressed, np.tile(predator, (p.I_p, 1))])


def deviation_gain(p: Params, rates: np.ndarray) -> float:
    """Most any predator could add by switching to its best response."""
    base = simulate(p, rates).payoff(p.mu)
    return max(simulate(p, best_response(p, rates, i, p.x_bar)).payoff(p.mu)[i] - base[i]
               for i in range(p.I_d, p.I))


def fictitious_play(p: Params, rates: np.ndarray, rounds: int, symmetric: bool = True,
                    record: tuple[int, ...] = ()) -> dict[int, np.ndarray]:
    """Damped best-response dynamics among predators."""
    rates = rates.copy()
    history = {}
    predators = range(p.I_d, p.I)
    for k in range(rounds):
        if symmetric:
            br = best_response(p, rates, p.I - 1, p.x_bar)[p.I - 1]
            responses = {i: br for i in predators}
        else:
            responses = {i: best_response(p, rates, i, p.x_bar)[i] for i in predators}
        step = 1 / (k + 2)
        for i, br in responses.items():
            rates[i] = (1 - step) * rates[i] + step * br
        if k + 1 in record or k + 1 == rounds:
            history[k + 1] = rates.copy()
    return history
