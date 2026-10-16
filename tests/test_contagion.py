"""Week 8, extension C: survival hurdles W(I_d) (eq. 21), Prop. 4, and the
Fig. 4 contagion scenarios. Six traders A-F as in Fig. 4."""

import numpy as np
import pytest

from contagion import cascade, equilibria, hurdles, others_when, survival_drop, wealth_change
from model import Params, simulate

P = Params(I=6, x_bar=6.0, x0=5.0, T=9.0, dt=0.005)  # S=40, mu=140, lam=1, A=20, t0=5


@pytest.fixture(scope="module")
def D():
    return hurdles(P)


def test_wealth_change_matches_the_simulator():
    # Trader i (row 0) sells to 2, then buys back to 6, against the I_d = 3 world.
    p = Params(**{**P.__dict__, "I_d": 3})
    others = others_when(p)
    x = survival_drop(p)[1]
    rates = np.vstack([np.diff(x) / p.dt, others])
    paths = simulate(p, rates)
    mark_to_market = paths.x[0] * paths.price + paths.cash[0] - p.x0 * paths.start_price
    np.testing.assert_allclose(wealth_change(p, others, x), mark_to_market, atol=1e-8)


def test_hurdle_values(D):
    # Any strategy allowed (eq. 21 literally). Pinned regression values; every
    # one was reached from 27 different starting paths, random ones included.
    np.testing.assert_allclose(D, [0, 0, 27, 48, 63, 72, 72], atol=1e-6)


def test_hurdle_values_without_buying():
    np.testing.assert_allclose(hurdles(P, can_buy=False), [0, 5, 34.5, 57, 70.5, 75, 75], atol=1e-6)


def test_prop4_survival_gets_harder_with_more_failures(D):
    assert all(a <= b + 1e-9 for a, b in zip(D, D[1:]))
    assert all(a < b for a, b in zip(D[1:6], D[2:6]))  # strictly up to I_d = 5
    # From 5 to 6 it is flat: with one predator left, it sells alongside the
    # distressed traders just as a sixth distressed trader would, so the
    # trough that trader i must survive is the same.


@pytest.mark.parametrize("I_d", [1, 3, 5])
def test_best_survival_beats_holding_and_selling(I_d):
    p = Params(**{**P.__dict__, "I_d": I_d})
    others = others_when(p)
    drop, x = survival_drop(p)
    n = others.shape[1]
    hold = -wealth_change(p, others, np.full(n + 1, p.x0)).min()
    assert drop <= hold + 1e-9
    assert -wealth_change(p, others, x).min() == pytest.approx(drop)


# Fig. 4: wealth levels relative to W_low = 100 and the hurdles W(1..6) =
# 100, 127, 148, 163, 172, 172. A in (W(1), W(2)], B in (W(2), W(3)],
# C in (W(3), W(4)], D, E, F safe.
W_LOW = 100.0
PANEL_A = np.array([115, 140, 155, 200, 200, 200], dtype=float)  # A..F


def test_panel_a_nobody_fails(D):
    assert equilibria(PANEL_A, W_LOW, D) == [0]
    assert cascade(PANEL_A, W_LOW, D) == [[]]


def test_panel_b_one_shock_allows_up_to_four_failures(D):
    # D is shocked below W_low. The paper: equilibria with 1, 2, 3 or 4 failures.
    wealth = PANEL_A.copy()
    wealth[3] = 90
    assert equilibria(wealth, W_LOW, D) == [1, 2, 3, 4]
    assert cascade(wealth, W_LOW, D) == [[3]]  # without panic, only D fails


def test_two_shocks_ripple_through_a_b_c(D):
    # D and E shocked: the paper's unique "ripple-effect" equilibrium.
    wealth = PANEL_A.copy()
    wealth[[3, 4]] = 90
    assert equilibria(wealth, W_LOW, D) == [5]
    assert cascade(wealth, W_LOW, D) == [[3, 4], [0, 3, 4], [0, 1, 3, 4], [0, 1, 2, 3, 4]]


def test_bailing_out_one_trader_stops_the_ripple(D):
    # Same two shocks, but a central bank recapitalises D.
    wealth = PANEL_A.copy()
    wealth[[3, 4]] = 90
    wealth[3] = 200
    assert cascade(wealth, W_LOW, D)[-1] == [4]
