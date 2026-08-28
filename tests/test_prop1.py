"""Prop. 1 against the paper's numerical example (Figs. 1-2), S=40, mu=140, lam=1,
A=20, x_bar=10, x(t0)=8, I=2, t0=5, T=7."""

import numpy as np
import pytest

from closed_form import orderly_value, paper_value, prop1_price, prop1_rates
from model import Params, schedule, simulate

P = Params()


@pytest.fixture(scope="module")
def paths():
    return simulate(P, prop1_rates(P))


def test_simulated_price_matches_eq18(paths):
    np.testing.assert_allclose(paths.price, prop1_price(P, paths.t), atol=1e-9)


def test_fig2_price_levels(paths):
    # 116 at t0, both sell 16 shares to 100 at 5.8, predator rebuilds to 110 at 6.3.
    for t, expected in [(5.0, 116), (5.8, 100), (6.3, 110), (7.0, 110)]:
        assert paths.price[paths.index(t)] == pytest.approx(expected)


def test_fig1_holdings(paths):
    distressed, predator = paths.x
    assert distressed[paths.index(5.8)] == pytest.approx(0)
    assert predator[paths.index(5.8)] == pytest.approx(0)
    assert predator[paths.index(6.3)] == pytest.approx(P.x_bar)


def test_selling_one_share_less_costs_half_a_point(paths):
    # Fig. 2 dotted line: predator sells 7 shares by 5.7, waits, then buys 9 by 6.25.
    predator = schedule(P, [(5.7, -10.0), (5.8, 0.0), (6.25, 20.0)])
    deviation = simulate(P, np.vstack([prop1_rates(P)[0], predator]))
    # The last share is sold at an average of 101.00 and bought back at 100.50.
    gain = paths.payoff(P.mu)[1] - deviation.payoff(P.mu)[1]
    assert gain == pytest.approx(0.5)


def test_several_distressed_one_predator():
    p = Params(I=3, I_d=2, x0=6.0, x_bar=10.0)
    paths = simulate(p, prop1_rates(p))
    assert np.all(np.abs(prop1_rates(p).sum(axis=0)) <= p.A + 1e-9)
    np.testing.assert_allclose(paths.x[:2, -1], 0, atol=1e-9)
    assert paths.x[2, -1] == pytest.approx(p.x_bar)
    np.testing.assert_allclose(paths.price, prop1_price(p, paths.t), atol=1e-9)


def test_assumptions_are_enforced():
    with pytest.raises(AssertionError, match="not enough time"):
        prop1_rates(Params(T=5.5))
    with pytest.raises(AssertionError, match="limited capital"):
        prop1_rates(Params(x_bar=25.0))


def test_valuation_ordering(paths):
    p_t0 = paths.price[0]
    distressed_value = paths.cash[0, -1]
    assert paper_value(p_t0, P.x0) == pytest.approx(928)
    assert orderly_value(P, p_t0, P.x0) == pytest.approx(896)
    assert distressed_value == pytest.approx(864)
