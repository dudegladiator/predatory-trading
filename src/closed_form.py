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


def prop7_x0(I: int, x_bar: float, pi: float, disclosed: bool) -> float:
    """Prop. 7, eqs. (22)-(23): position built before t0, when a random trader
    becomes distressed with probability pi."""
    if I == 2 or disclosed:
        return (1 - pi / (I - 1)) * x_bar
    return (1 - pi / I) * x_bar


def prop8_tau(p: Params) -> float:
    """Prop. 8: how long predators front-run, selling at A/I_p from t0."""
    return ((p.I - 1) * p.x0 - p.x_bar * (p.I_p - 1)) / (p.A * (p.I_p - 1) / p.I_p)


def prop8_rates(p: Params, t1: float) -> np.ndarray:
    """Prop. 8, eq. (24): distressed traders only start selling at t1 > t0."""
    assert p.I_p >= 2 and preys(p)
    tau = prop8_tau(p)
    end = t1 + p.x0 / (p.A / p.I)
    assert p.t0 + tau <= t1, "front-running must end before the distressed start selling"
    assert p.x0 - p.A * tau / p.I_p >= -p.x_bar - 1e-12, "front-running breaks the position limit"
    _check_assumptions(p, end)
    distressed = schedule(p, [(t1, 0.0), (end, -p.A / p.I)])
    predator = schedule(p, [(p.t0 + tau, -p.A / p.I_p), (t1, 0.0),
                            (end, p.A * p.I_d / (p.I * (p.I_p - 1)))])
    return _stack(p, distressed, predator)


def prop8_price(p: Params, t1: float, t: np.ndarray) -> np.ndarray:
    """Prop. 8, eq. (25): price path with front-running."""
    tau = prop8_tau(p)
    p_t0 = p.price(p.I * p.x0)
    return np.select(
        [t < p.t0 + tau, t < t1, t < t1 + p.x0 / (p.A / p.I)],
        [p_t0 - p.lam * p.A * (t - p.t0),
         np.full_like(t, p_t0 - p.lam * p.A * tau),
         p_t0 - p.lam * p.A * tau + p.lam * p.A * p.I_d / (p.I * (p.I_p - 1)) * (t - t1)],
        p.mu + p.lam * (p.x_bar * p.I_p - p.S),
    )


def prop9_trades(p: Params) -> tuple[np.ndarray, np.ndarray]:
    """Prop. 9: batch auction at t0. Returns (auction block trades, rates after)."""
    assert preys(p)
    _check_assumptions(p, p.t0 + (p.x_bar - p.x0) / p.A)
    auction = np.concatenate([np.full(p.I_d, -p.x0),
                              np.full(p.I_p, (p.I_p - 1) / p.I_p * (p.x_bar - p.x0))])
    predator = schedule(p, [(p.t0 + (p.x_bar - p.x0) / p.A, p.A / p.I_p)])
    return auction, _stack(p, np.zeros_like(predator), predator)


def prop9_price(p: Params, t: np.ndarray) -> np.ndarray:
    """Prop. 9, eq. (26): price path with a batch auction at t0."""
    auction_price = p.mu - p.lam * p.S + p.lam * (p.I_p - 1) * p.x_bar + p.lam * p.x0
    return np.where(t < p.t0 + (p.x_bar - p.x0) / p.A,
                    auction_price + p.lam * p.A * (t - p.t0),
                    p.mu - p.lam * p.S + p.lam * p.I_p * p.x_bar)


def paper_value(price: float, x: float) -> float:
    """Def. 2 (i): mark-to-market value."""
    return x * price


def orderly_value(p: Params, price: float, x: float) -> float:
    """Def. 2 (ii): revenue from a secret liquidation down the demand curve."""
    return x * (price - p.lam * x / 2)
