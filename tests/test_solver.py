"""Weeks 5-6: the LP best response and fictitious play confirm the paper's equilibria.

Holding the other traders at the paper's strategies, no predator can do better
than the paper's strategy: the LP optimum pays exactly the same.
"""

import numpy as np
import pytest

from closed_form import (
    equilibrium_rates,
    liquidation_end,
    prop2_price,
    prop2_tau,
    prop8_rates,
)
from model import Params, schedule, simulate, speed_caps
from solver import best_response, deviation_gain, fictitious_play, naive_start


def caps(*others, A=20.0):
    lo, hi = speed_caps(np.array(others, dtype=float)[:, None], A)
    return lo[0], hi[0]


def test_speed_caps():
    # Prop. 1: the distressed trader sells at 10. The predator can sell at most 10
    # more, and could buy up to 30 (net market flow +20).
    assert caps(-10) == pytest.approx((-10, 30))
    # Nobody else trading: the whole limit A either way.
    assert caps(0, 0) == pytest.approx((-20, 20))
    # Equal priority, not first come first served: another trader buying 15 still
    # leaves trader i a buying share of 10 (y + min(15, y) = 20).
    assert caps(15) == pytest.approx((-35, 10))
    # Prop. 2, I = 3: two others selling at A/3 cap trader i's selling at A/3.
    assert caps(-20 / 3, -20 / 3)[0] == pytest.approx(-20 / 3)


def check_equilibrium(p: Params, rates: np.ndarray) -> list[np.ndarray]:
    """For each predator: LP best response pays the same as the given strategy."""
    base = simulate(p, rates).payoff(p.mu)
    responses = []
    for i in range(p.I_d, p.I):
        br = best_response(p, rates, i, target=p.x_bar)
        assert simulate(p, br).payoff(p.mu)[i] == pytest.approx(base[i], abs=1e-6)
        responses.append(br)
    return responses


def test_prop1_is_a_best_response():
    p = Params()
    (br,) = check_equilibrium(p, equilibrium_rates(p))
    # Footnote 13: the buy-back speed is free, but any best response must have
    # sold everything by the time the distressed trader is out.
    x = simulate(p, br).x[1]
    assert x[round((liquidation_end(p) - p.t0) / p.dt)] == pytest.approx(0, abs=1e-9)


@pytest.mark.parametrize("I", [3, 9])
def test_prop2_is_a_best_response(I):
    p = Params(I=I, I_d=I // 3, x0=16 / I, x_bar=20 / I)
    rates = equilibrium_rates(p)
    responses = check_equilibrium(p, rates)
    # The predator must sell for exactly tau, as in the paper.
    k = round(prop2_tau(p) / p.dt)
    for i, br in zip(range(p.I_d, p.I), responses):
        assert simulate(p, br).x[i, k] == pytest.approx(simulate(p, rates).x[i, k], abs=1e-9)


def test_prop2_prime_is_a_best_response():
    p = Params(I=3, I_d=1, x0=4.0, x_bar=10.0)
    check_equilibrium(p, equilibrium_rates(p))


def test_prop8_front_running_is_a_best_response():
    p = Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3)
    check_equilibrium(p, prop8_rates(p, t1=5.5))


def test_lp_beats_a_non_equilibrium_strategy():
    # Predator just buys from t0 instead of preying: the LP finds the predatory
    # strategy, worth the paper's equilibrium payoff.
    p = Params()
    naive = equilibrium_rates(p)
    naive[1] = schedule(p, [(p.t0 + (p.x_bar - p.x0) / 10, 10.0)])
    br = best_response(p, naive, 1, target=p.x_bar)
    gain = simulate(p, br).payoff(p.mu)[1] - simulate(p, naive).payoff(p.mu)[1]
    assert gain > 1
    equilibrium = simulate(p, equilibrium_rates(p)).payoff(p.mu)[1]
    assert simulate(p, br).payoff(p.mu)[1] == pytest.approx(equilibrium, abs=1e-6)


@pytest.mark.parametrize("p", [
    Params(),
    Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3),
    Params(I=3, I_d=1, x0=4.0, x_bar=10.0),
])
def test_ending_at_capacity_is_optimal(p):
    # Lemma 1 imposes x_i(T) = x_bar; check it: the best payoff for each end
    # position rises all the way up to x_bar.
    rates, i = equilibrium_rates(p), p.I - 1
    payoffs = [simulate(p, best_response(p, rates, i, x)).payoff(p.mu)[i]
               for x in np.linspace(-p.x_bar, p.x_bar, 9)]
    assert all(a < b for a, b in zip(payoffs, payoffs[1:]))


def test_best_response_respects_constraints():
    p = Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3)
    rates = equilibrium_rates(p)
    br = best_response(p, rates, 2, target=p.x_bar)
    lo, hi = speed_caps(np.delete(br, 2, axis=0), p.A)
    assert np.all(br[2] >= lo - 1e-7) and np.all(br[2] <= hi + 1e-7)
    assert np.all(np.abs(simulate(p, br).x[2]) <= p.x_bar + 1e-9)


# Week 6: fictitious play from a naive start converges to Prop. 2.

FIG3_I3 = Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3)


def test_paper_equilibrium_has_no_profitable_deviation():
    for p in (Params(), FIG3_I3, Params(I=9, I_d=3, x0=16 / 9, x_bar=20 / 9)):
        assert abs(deviation_gain(p, equilibrium_rates(p))) < 1e-6


def test_symmetric_fictitious_play_converges_to_prop2():
    p = FIG3_I3
    start = naive_start(p, equilibrium_rates(p)[: p.I_d])
    history = fictitious_play(p, start, rounds=300, record=(10, 50, 100))
    gains = [deviation_gain(p, start)] + [deviation_gain(p, history[k]) for k in (10, 50, 100, 300)]
    assert gains[0] > 20                               # naive start is far from equilibrium
    assert all(a > b for a, b in zip(gains, gains[1:]))  # steadily closer
    assert gains[-1] < 0.3
    paths = simulate(p, history[300])
    target = prop2_price(p, paths.t)
    assert np.abs(paths.price - target).max() < 0.6     # price path close to eq. (20)


def test_asymmetric_fictitious_play_ends_symmetric():
    # Two predators start from different strategies and respond separately; both
    # head to the paper's symmetric position at t0 + tau (3.333 each).
    p = FIG3_I3
    rates = naive_start(p, equilibrium_rates(p)[: p.I_d])
    rates[2] = schedule(p, [(6.5, 0.0), (p.T, (p.x_bar - p.x0) / 0.5)])  # waits, buys late
    final = fictitious_play(p, rates, rounds=100, symmetric=False)[100]
    x = simulate(p, final).x
    k = round(prop2_tau(p) / p.dt)
    np.testing.assert_allclose(x[1:, k], simulate(p, equilibrium_rates(p)).x[1:, k], atol=0.05)
