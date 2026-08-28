"""Closed-form equilibrium strategies and values from the paper.

Rate functions return an (I, N) array: distressed traders first (indices
0 .. I_d - 1), then predators.
"""

import numpy as np

from model import Params, schedule


def liquidation_end(p: Params) -> float:
    """Time at which distressed traders, selling at A/I, are out."""
    return p.t0 + p.x0 / (p.A / p.I)


def _check_assumptions(p: Params, finish: float) -> None:
    """The paper's standing assumptions behind the equilibrium."""
    assert p.x_bar * p.I < p.S, "limited capital: I x_bar < S (Section I)"
    assert finish <= p.T + 1e-12, "not enough time to trade before T"


def _stack(p: Params, distressed: np.ndarray, predator: np.ndarray) -> np.ndarray:
    return np.vstack([np.tile(distressed, (p.I_d, 1)), np.tile(predator, (p.I_p, 1))])


def prop1_rates(p: Params) -> np.ndarray:
    """Prop. 1, eq. (17): one predator, I - 1 distressed traders.

    Everyone sells at A/I until the distressed traders are out; the predator
    then buys back at A until it holds x_bar.
    """
    assert p.I_p == 1
    end = liquidation_end(p)
    _check_assumptions(p, end + p.x_bar / p.A)
    distressed = schedule(p, [(end, -p.A / p.I)])
    predator = schedule(p, [(end, -p.A / p.I), (end + p.x_bar / p.A, p.A)])
    return _stack(p, distressed, predator)


def prop1_price(p: Params, t: np.ndarray) -> np.ndarray:
    """Prop. 1, eq. (18): equilibrium price path."""
    end = liquidation_end(p)
    p_t0 = p.price(p.I * p.x0)
    return np.select(
        [t < end, t < end + p.x_bar / p.A],
        [p_t0 - p.lam * p.A * (t - p.t0),
         p_t0 - p.lam * p.I * p.x0 + p.lam * p.A * (t - end)],
        p.mu + p.lam * (p.x_bar - p.S),
    )


def paper_value(price: float, x: float) -> float:
    """Def. 2 (i): mark-to-market value."""
    return x * price


def orderly_value(p: Params, price: float, x: float) -> float:
    """Def. 2 (ii): revenue from a secret liquidation down the demand curve."""
    return x * (price - p.lam * x / 2)
