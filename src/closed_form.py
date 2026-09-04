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


def preys(p: Params) -> bool:
    """Prop. 2 vs 2': predators prey iff x0 >= (I_p - 1) / (I - 1) * x_bar."""
    return p.x0 >= (p.I_p - 1) / (p.I - 1) * p.x_bar


def prop2_tau(p: Params) -> float:
    """Prop. 2: how long predators sell before buying back."""
    return (p.x0 - (p.I_p - 1) / (p.I - 1) * p.x_bar) / (p.A / p.I)


def prop2_rates(p: Params) -> np.ndarray:
    """Prop. 2, eq. (19): I_p >= 2 predators prey.

    Predators sell at A/I for tau, then buy at A I_d / (I (I_p - 1)) so that each
    predator's X_{-i} stays flat until the distressed traders are out.
    """
    assert p.I_p >= 2 and preys(p)
    end = liquidation_end(p)
    _check_assumptions(p, end)
    distressed = schedule(p, [(end, -p.A / p.I)])
    predator = schedule(p, [(p.t0 + prop2_tau(p), -p.A / p.I),
                            (end, p.A * p.I_d / (p.I * (p.I_p - 1)))])
    return _stack(p, distressed, predator)


def prop2_price(p: Params, t: np.ndarray) -> np.ndarray:
    """Prop. 2, eq. (20): equilibrium price path."""
    tau = prop2_tau(p)
    p_t0 = p.price(p.I * p.x0)
    return np.select(
        [t < p.t0 + tau, t < liquidation_end(p)],
        [p_t0 - p.lam * p.A * (t - p.t0),
         p_t0 - p.lam * p.A * tau
         + p.lam * p.A * p.I_d / (p.I * (p.I_p - 1)) * (t - (p.t0 + tau))],
        p.mu + p.lam * (p.x_bar * p.I_p - p.S),
    )


def prop2_prime_rates(p: Params) -> np.ndarray:
    """Prop. 2': predators have spare capacity and buy from t0 (no predation).

    They first buy at A (I + I_d) / (I_p I), using all of the market's capacity,
    until each predator's X_{-i} reaches its final level (I_p - 1) x_bar; then at
    A I_d / (I (I_p - 1)), absorbing exactly the distressed selling.
    """
    assert p.I_p >= 2 and not preys(p)
    end = liquidation_end(p)
    _check_assumptions(p, end)
    tau = (((p.I_p - 1) * p.x_bar - (p.I - 1) * p.x0)
           / (p.A * (1 - (p.I + p.I_d) / (p.I_p * p.I))))
    assert p.t0 + tau <= end
    distressed = schedule(p, [(end, -p.A / p.I)])
    predator = schedule(p, [(p.t0 + tau, p.A * (p.I + p.I_d) / (p.I_p * p.I)),
                            (end, p.A * p.I_d / (p.I * (p.I_p - 1)))])
    return _stack(p, distressed, predator)


def equilibrium_rates(p: Params) -> np.ndarray:
    """Equilibrium of the predatory phase for any number of predators."""
    if p.I_p == 1:
        return prop1_rates(p)
    return prop2_rates(p) if preys(p) else prop2_prime_rates(p)


def paper_value(price: float, x: float) -> float:
    """Def. 2 (i): mark-to-market value."""
    return x * price


def orderly_value(p: Params, price: float, x: float) -> float:
    """Def. 2 (ii): revenue from a secret liquidation down the demand curve."""
    return x * (price - p.lam * x / 2)
