"""Eq. (8): the temporary impact cost G for trading faster than the speed caps."""

import numpy as np
import pytest

from closed_form import equilibrium_rates, prop8_rates
from model import Params, impact_costs, schedule, simulate, speed_caps
from solver import fictitious_play, naive_start


def test_hand_computed_charge():
    # Prop. 1 setting: distressed sells at 10; the predator sells at 20 for 0.1,
    # 10 above its cap of 10. G = gamma * 10 per unit time, gamma = lam I x_bar = 20.
    p = Params()
    rates = equilibrium_rates(p)
    rates[1] = schedule(p, [(5.1, -20.0), (5.8, -10.0), (6.4, 20.0)])
    cost = impact_costs(p, rates)
    assert cost[0].sum() == 0
    assert cost[1].sum() * p.dt == pytest.approx(20 * 10 * 0.1)


@pytest.mark.parametrize("p", [Params(), Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3),
                               Params(I=9, I_d=3, x0=16 / 9, x_bar=20 / 9)])
def test_equilibria_pay_nothing(p):
    assert np.all(impact_costs(p, equilibrium_rates(p)) == 0)
    if p.I_p >= 2:
        assert np.all(impact_costs(p, prop8_rates(p, 5.5)) == 0)


def test_total_within_A_means_nobody_exceeds_their_cap():
    # The shortcut in impact_costs: |Σ a| <= A  =>  every a_i within its caps.
    rng = np.random.default_rng(0)
    A = 20.0
    for _ in range(2000):
        a = rng.normal(0, 15, size=rng.integers(2, 8))
        if abs(a.sum()) > A:
            continue
        for i in range(len(a)):
            lo, hi = speed_caps(np.delete(a, i)[:, None], A)
            assert lo[0] - 1e-9 <= a[i] <= hi[0] + 1e-9


def test_early_learning_rounds_are_charged():
    # Symmetric fictitious play with 6 predators: in round 1 all of them adopt a
    # best response that was only feasible for one, so the market trades at 60.
    p = Params(I=9, I_d=3, x0=16 / 9, x_bar=20 / 9)
    rates = fictitious_play(p, naive_start(p, equilibrium_rates(p)[: p.I_d]), rounds=1)[1]
    assert np.abs(rates.sum(axis=0)).max() == pytest.approx(60)
    assert impact_costs(p, rates)[p.I_d:].sum() > 0
