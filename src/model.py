"""Market model of Brunnermeier & Pedersen (2005), Section I, in discrete time.

Trading rates are piecewise constant on a grid t0, t0 + dt, ..., T. The price is
linear in holdings and holdings are linear within a step, so the cash computed
here equals the paper's integral of a(t) p(t) dt exactly when strategy switch
times fall on the grid (and is off by O(dt^2) per switch otherwise).

Trading faster than the equal-priority speed caps (eqs. 9-10) costs the
temporary impact cost G of eq. (8), charged at gamma = lam * I * x_bar per
excess share, the smallest gamma the paper allows. The paper's equilibria
never pay it; off-equilibrium strategies (e.g. during learning) can.
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
    # Per-trader holdings at t0, overriding x0 (week 9, unequal positions).
    holdings: tuple[float, ...] | None = None

    @property
    def I_p(self) -> int:
        return self.I - self.I_d

    def start(self) -> np.ndarray:
        """Each trader's holdings at t0."""
        return np.full(self.I, self.x0) if self.holdings is None else np.array(self.holdings)

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


def _buy_cap(others: np.ndarray, A: float) -> np.ndarray:
    """Eq. (9): solve y + Σ_j min(a_j, y) = A per step. others is (m, N).

    If exactly k of the others trade below y, the left side is
    (m - k + 1) y + (sum of those k rates); try every k and keep the one
    whose y lands between the k-th and (k+1)-th smallest rate.
    """
    s = np.sort(others, axis=0)
    m, n = s.shape
    prefix = np.vstack([np.zeros(n), np.cumsum(s, axis=0)])
    k = np.arange(m + 1)[:, None]
    y = (A - prefix) / (m - k + 1)
    lower = np.vstack([np.full(n, -np.inf), s])
    upper = np.vstack([s, np.full(n, np.inf)])
    valid = (y >= lower - 1e-12) & (y <= upper + 1e-12)
    return y[np.argmax(valid, axis=0), np.arange(n)]


def speed_caps(others: np.ndarray, A: float) -> tuple[np.ndarray, np.ndarray]:
    """Eqs. (9)-(10): fastest sell and buy rates for trader i per step without
    temporary impact cost, given the other traders' rates (m, N).

    The paper prints eq. (10) as "= A"; it must be "= -A" to match eq. (7)
    and Prop. 1, so the sell cap is the mirror image of the buy cap.
    """
    return -_buy_cap(-others, A), _buy_cap(others, A)


def impact_costs(p: Params, rates: np.ndarray) -> np.ndarray:
    """Eq. (8): G per trader per step, as a rate (multiply by dt for cash).

    If |Σ a| <= A, nobody exceeds their cap: a_i > ā_i would give
    a_i + Σ_j a_j >= a_i + Σ_j min(a_j, a_i) > A. So caps are only computed at
    steps where the market as a whole trades too fast.
    """
    cost = np.zeros_like(rates)
    over = np.abs(rates.sum(axis=0)) > p.A + 1e-9
    if over.any():
        gamma = p.lam * p.I * p.x_bar
        for i in range(p.I):
            lo, hi = speed_caps(np.delete(rates[:, over], i, axis=0), p.A)
            a = rates[i, over]
            excess = np.maximum(a - hi, lo - a)
            cost[i, over] = gamma * np.where(excess > 1e-9, excess, 0.0)  # ignore rounding
    return cost


@dataclass
class Paths:
    t: np.ndarray      # (N + 1,)
    x: np.ndarray      # (I, N + 1) holdings
    price: np.ndarray  # (N + 1,)
    cash: np.ndarray   # (I, N + 1) cumulative -∫ (a p + G) dt
    start_price: float  # price at t0 before any batch auction

    def index(self, t: float) -> int:
        return int(round((t - self.t[0]) / (self.t[1] - self.t[0])))

    def overshoot(self) -> float:
        """How far the price falls below both its starting and long-run levels."""
        return max(0.0, min(self.start_price, self.price[-1]) - self.price.min())

    def payoff(self, mu: float) -> np.ndarray:
        """Expected final wealth of each trader, objective (11)."""
        return self.x[:, -1] * mu + self.cash[:, -1]


def simulate(p: Params, rates: np.ndarray, auction: np.ndarray | None = None) -> Paths:
    """rates[i, k] is trader i's trading intensity on [t_k, t_k + dt).

    auction[i] is an optional block trade at t0 in a batch auction (Section VI.B):
    all orders execute at the single price that clears the demand curve.
    """
    t = time_grid(p)
    start = p.start() if auction is None else p.start() + auction
    steps = rates * p.dt
    x = start[:, None] + np.concatenate([np.zeros((p.I, 1)), np.cumsum(steps, axis=1)], axis=1)
    price = p.price(x.sum(axis=0))
    # Price is linear within a step, so its average there is the trapezoid.
    spent = steps * (price[:-1] + price[1:]) / 2
    spent += impact_costs(p, rates) * p.dt
    cash = -np.concatenate([np.zeros((p.I, 1)), np.cumsum(spent, axis=1)], axis=1)
    if auction is not None:
        cash -= (auction * price[0])[:, None]
    return Paths(t=t, x=x, price=price, cash=cash, start_price=p.price(p.start().sum()))
