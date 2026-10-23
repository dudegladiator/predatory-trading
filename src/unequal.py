"""Week 9 (stretch A): predators with unequal positions at t0 (footnote 15).

The paper describes this equilibrium only in words:
- Everyone sells at A/I until the X₋ᵢ of the predator with the *smallest*
  position falls to its final level (I_p - 1) x_bar, at time s.
- Then predators buy at I_d A / (I (m - 1)) each, where m is the number still
  buying, which keeps each buyer's X₋ᵢ flat. As predators reach x_bar and
  stop, the rest speed up.
The footnote leaves out the last buyer (m = 1). Here it waits until the
distressed traders are out, then buys at the full speed A. The LP solver
confirms this strategy is an equilibrium (tests/test_unequal.py).

Distressed traders come first in p.holdings; all are assumed to hold the same.
"""

import numpy as np

from model import Params, time_grid


def switch_time(p: Params) -> float:
    """When the smallest predator's X₋ᵢ reaches (I_p - 1) x_bar."""
    h = p.start()
    return p.t0 + (h.sum() - h[p.I_d:].min() - (p.I_p - 1) * p.x_bar) / ((p.I - 1) * p.A / p.I)


def predicted_overshoot(p: Params) -> float:
    """Derived here, not in the paper: the trough is at s, so the overshoot is
    λ [A (s - t0) - (X0 - I_p x_bar)]. It depends on the positions only through
    the smallest predator's (via s) and the total X0."""
    return p.lam * (p.A * (switch_time(p) - p.t0) - (p.start().sum() - p.I_p * p.x_bar))


def footnote15_rates(p: Params) -> np.ndarray:
    """Footnote 15's strategies, built step by step on the grid."""
    h = p.start()
    assert p.I_p >= 2 and np.all(np.abs(h) <= p.x_bar), "needs >= 2 predators within the limit"
    assert np.allclose(h[: p.I_d], h[0]), "distressed traders are assumed to hold the same"
    s = switch_time(p)
    end = p.t0 + h[0] / (p.A / p.I)
    assert p.t0 <= s <= end, "predators must prey (Prop. 2 regime) and switch before the distressed are out"
    assert h[p.I_d:].min() - p.A / p.I * (s - p.t0) >= -p.x_bar, "selling would break the position limit"

    t = time_grid(p)
    x = h.astype(float)
    rates = np.zeros((p.I, len(t) - 1))
    for k in range(len(t) - 1):
        r = np.zeros(p.I)
        r[: p.I_d] = -np.minimum(p.A / p.I, x[: p.I_d] / p.dt)
        selling = int(np.sum(x[: p.I_d] > 1e-12))
        buyers = [i for i in range(p.I_d, p.I) if x[i] < p.x_bar - 1e-12]
        sell_part = min(max(s - t[k], 0.0), p.dt) / p.dt  # share of the step before s
        for i in range(p.I_d, p.I):
            if i in buyers and selling and len(buyers) >= 2:
                buy = selling * (p.A / p.I) / (len(buyers) - 1)
            elif i in buyers and not selling:
                buy = p.A / len(buyers)
            else:
                buy = 0.0  # done, or the last buyer waiting for the distressed
            rate = sell_part * (-p.A / p.I) + (1 - sell_part) * buy
            r[i] = min(rate, (p.x_bar - x[i]) / p.dt)
        rates[:, k] = r
        x = x + r * p.dt
    return rates
