"""Numerical best responses: Lemma 1 turned into a linear program.

With x_i(0) and x_i(T) fixed, trader i's payoff (11) on the grid equals a
constant minus  λ Σ_k a_k dt · (X₋ᵢ,k + X₋ᵢ,k+1) / 2,  where X₋ᵢ is everyone
else's holdings. That is linear in trader i's holdings path, so the best
response to fixed opponents is an LP, and its optimum is exact for the
discretized game (not an approximation of it).
"""

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import diags, vstack

from model import Params, schedule, simulate, speed_caps


def _optimal_holdings(p: Params, others: np.ndarray, others_start: float,
                      start: float, target: float, limit: float) -> np.ndarray:
    """LP: best holdings path x_0..x_N of one trader (or a coordinated group
    acting as one) against the fixed rates of `others`, from `start` to
    `target`, within |x| <= limit and the speed caps."""
    n = others.shape[1]
    X = others_start + np.concatenate([[0.0], np.cumsum(others.sum(axis=0) * p.dt)])
    w = (X[:-1] + X[1:]) / 2
    # Variables are holdings x_0..x_N; cost Σ_k (x_{k+1} - x_k) w_k.
    c = np.concatenate([[0.0], w]) - np.concatenate([w, [0.0]])
    lo, hi = speed_caps(others, p.A)
    D = diags([-np.ones(n), np.ones(n)], [0, 1], shape=(n, n + 1))
    bounds = [(start, start)] + [(-limit, limit)] * (n - 1) + [(target, target)]
    res = linprog(c, A_ub=vstack([D, -D]), b_ub=np.concatenate([hi * p.dt, -lo * p.dt]),
                  bounds=bounds, method="highs")
    assert res.status == 0, res.message
    return res.x


def best_response(p: Params, rates: np.ndarray, i: int, target: float) -> np.ndarray:
    """Trader i's payoff-maximising rates with everyone else's held fixed.

    Ends at x_i(T) = target (x_bar for a predator, Lemma 1), stays within
    |x_i| <= x_bar and within the speed caps. Returns `rates` with row i replaced.
    """
    start = p.start()
    x = _optimal_holdings(p, np.delete(rates, i, axis=0), start.sum() - start[i],
                          start[i], target, p.x_bar)
    out = rates.copy()
    out[i] = np.diff(x) / p.dt
    return out


def collusive_response(p: Params, rates: np.ndarray) -> np.ndarray:
    """Week 7 (extension F): predators maximise their *joint* profit against
    the distressed traders' fixed strategy.

    The same algebra as Lemma 1 applies to the group's total holdings P: its
    total payoff is a constant minus λ ∫ (dP/dt) · (distressed holdings) dt. So
    the cartel is one LP for a single trader with capacity I_p x_bar. Eq. (9)
    for the group as one trader gives the same speed cap as the sum of its
    members' caps when they trade equally, so the trades are split equally.
    """
    assert p.holdings is None, "the cartel solver assumes equal holdings"
    x = _optimal_holdings(p, rates[: p.I_d], p.x0 * p.I_d,
                          p.x0 * p.I_p, p.x_bar * p.I_p, p.x_bar * p.I_p)
    out = rates.copy()
    out[p.I_d:] = np.diff(x) / p.dt / p.I_p
    return out


def naive_start(p: Params, distressed: np.ndarray) -> np.ndarray:
    """Starting point for the dynamics: predators simply buy steadily up to x_bar
    while the distressed traders sell (no predation). distressed is (I_d, N)."""
    end = p.t0 + p.x0 / (p.A / p.I)
    predator = schedule(p, [(end, (p.x_bar - p.x0) / (end - p.t0))])
    return np.vstack([distressed, np.tile(predator, (p.I_p, 1))])


def deviation_gain(p: Params, rates: np.ndarray) -> float:
    """Most any predator could add to its payoff by switching to its best
    response. Zero exactly at an equilibrium."""
    base = simulate(p, rates).payoff(p.mu)
    return max(simulate(p, best_response(p, rates, i, p.x_bar)).payoff(p.mu)[i] - base[i]
               for i in range(p.I_d, p.I))


def fictitious_play(p: Params, rates: np.ndarray, rounds: int, symmetric: bool = True,
                    record: tuple[int, ...] = ()) -> dict[int, np.ndarray]:
    """Damped best-response dynamics among the predators; distressed traders
    keep their rows of `rates`.

    Each round every predator moves a step 1/(k + 2) of the way toward its best
    response (classic fictitious play). Plain best responses cycle, because they
    are all-or-nothing. symmetric=True keeps all predators on one shared
    strategy (one LP per round); otherwise each responds to the others
    separately, simultaneously. Returns the rates after each round in `record`
    and after the last round.
    """
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
