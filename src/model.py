"""Market model of Brunnermeier & Pedersen (2005), Section I, in discrete time.

Trading rates are piecewise constant on a grid t0, t0 + dt, ..., T. The price is
linear in holdings and holdings are linear within a step, so the cash computed
here equals the paper's integral of a(t) p(t) dt exactly when strategy switch
times fall on the grid (and is off by O(dt^2) per switch otherwise).
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Params:
    S: float = 40.0      # aggregate supply of the risky asset
    mu: float = 140.0    # expected final payoff E(v)
    lam: float = 1.0     # price impact per share (illiquidity)
    A: float = 20.0      # total trading speed without temporary impact cost
    x_bar: float = 10.0  # position limit of each strategic trader
    x0: float = 8.0      # common holding of every strategic trader at t0
    I: int = 2           # number of strategic traders
    I_d: int = 1         # number of distressed traders (indices 0 .. I_d - 1)
    t0: float = 5.0
    T: float = 7.0
    dt: float = 0.001

    @property
    def I_p(self) -> int:
        return self.I - self.I_d

    def price(self, X):
        """Eq. (6): p = mu - lam (S - X), X = total strategic holdings."""
        return self.mu - self.lam * (self.S - X)


def time_grid(p: Params) -> np.ndarray:
    n = round((p.T - p.t0) / p.dt)
    return p.t0 + p.dt * np.arange(n + 1)


def schedule(p: Params, phases: list[tuple[float, float]]) -> np.ndarray:
    """Per-step rates of a strategy trading at rate r_j until time end_j.

    phases = [(end_1, r_1), (end_2, r_2), ...] runs from t0, with rate 0 after
    the last end. Each step gets the strategy's average rate over that step, so
    holdings are exact on the grid even when a switch falls inside a step.
    """
    knots, volume, start = [p.t0], [0.0], p.t0
    for end, rate in phases:
        if end > start:
            knots.append(end)
            volume.append(volume[-1] + rate * (end - start))
            start = end
    return np.diff(np.interp(time_grid(p), knots, volume)) / p.dt


@dataclass
class Paths:
    t: np.ndarray      # (N + 1,)
    x: np.ndarray      # (I, N + 1) holdings
    price: np.ndarray  # (N + 1,)
    cash: np.ndarray   # (I, N + 1) cumulative -integral a p dt

    def index(self, t: float) -> int:
        return int(round((t - self.t[0]) / (self.t[1] - self.t[0])))

    def payoff(self, mu: float) -> np.ndarray:
        """Expected final wealth of each trader, objective (11)."""
        return self.x[:, -1] * mu + self.cash[:, -1]


def simulate(p: Params, rates: np.ndarray) -> Paths:
    """rates[i, k] is trader i's trading intensity on [t_k, t_k + dt)."""
    t = time_grid(p)
    steps = rates * p.dt
    x = p.x0 + np.concatenate([np.zeros((p.I, 1)), np.cumsum(steps, axis=1)], axis=1)
    price = p.price(x.sum(axis=0))
    # Price is linear within a step, so its average there is the trapezoid.
    spent = steps * (price[:-1] + price[1:]) / 2
    cash = -np.concatenate([np.zeros((p.I, 1)), np.cumsum(spent, axis=1)], axis=1)
    return Paths(t=t, x=x, price=price, cash=cash)
