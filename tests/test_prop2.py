"""Props. 2, 2' and 3 against the paper's Fig. 3 example: a third of I traders
distressed, total holding I x(t0) = 16, total capacity I x_bar = 20."""

import numpy as np
import pytest

from closed_form import (
    equilibrium_rates,
    liquidation_end,
    prop2_price,
    prop2_prime_rates,
    prop2_rates,
    prop2_tau,
)
from model import Params, simulate


def fig3_params(I: int, dt: float = 0.001) -> Params:
    return Params(I=I, I_d=I // 3, x0=16 / I, x_bar=20 / I, dt=dt)


@pytest.mark.parametrize("I", [3, 9, 27])
def test_simulated_price_matches_eq20(I):
    p = fig3_params(I)
    paths = simulate(p, prop2_rates(p))
    np.testing.assert_allclose(paths.price, prop2_price(p, paths.t), atol=1e-9)


@pytest.mark.parametrize("I, lowest", [(3, 110.0), (9, 112.5), (27, 113.077)])
def test_fig3_price_levels(I, lowest):
    p = fig3_params(I)
    paths = simulate(p, prop2_rates(p))
    # Long-run price mu + lam (I_p x_bar - S) = 140 + 40/3 - 40.
    assert paths.price[-1] == pytest.approx(113.333, abs=1e-3)
    # I = 27's trough falls between grid points: allow one step of price movement.
    assert paths.price.min() == pytest.approx(lowest, abs=p.lam * p.A * p.dt)


@pytest.mark.parametrize("I", [3, 9, 27])
def test_predators_end_at_capacity_when_distressed_are_out(I):
    p = fig3_params(I)
    paths = simulate(p, prop2_rates(p))
    end = paths.index(liquidation_end(p))
    np.testing.assert_allclose(paths.x[: p.I_d, end], 0, atol=1e-9)
    np.testing.assert_allclose(paths.x[p.I_d :, end], p.x_bar, atol=1e-9)


def test_prop3_overshoot_positive_decreasing_vanishing():
    # Overshoot from eq. (20) exactly: long-run price minus the price at t0 + tau.
    def overshoot(I):
        p = fig3_params(I)
        t = np.array([p.t0 + prop2_tau(p), p.T])
        low, long_run = prop2_price(p, t)
        return long_run - low

    values = [overshoot(3 * k) for k in range(1, 50)]
    assert all(v > 0 for v in values)
    assert all(a > b for a, b in zip(values, values[1:]))
    assert overshoot(3 * 10_000) < 1e-3


def test_prop2_prime_no_predation():
    # Plenty of sidelined capacity: x0 = 4 < (I_p - 1)/(I - 1) x_bar = 5.
    p = Params(I=3, I_d=1, x0=4.0, x_bar=10.0)
    paths = simulate(p, prop2_prime_rates(p))
    assert np.all(np.diff(paths.price) >= -1e-12)  # price never falls
    assert paths.overshoot() == pytest.approx(0)
    end = paths.index(liquidation_end(p))
    np.testing.assert_allclose(paths.x[p.I_d :, end], p.x_bar, atol=1e-9)
    assert paths.price[-1] == pytest.approx(p.mu + p.lam * (p.I_p * p.x_bar - p.S))


def test_total_speed_never_exceeds_A():
    for p in [Params(), fig3_params(3), fig3_params(27), Params(I=3, I_d=1, x0=4.0)]:
        assert np.all(np.abs(equilibrium_rates(p).sum(axis=0)) <= p.A + 1e-9)
