"""Week 5: the LP best response confirms the paper's equilibria."""

import numpy as np
import pytest

from closed_form import equilibrium_rates, liquidation_end, prop2_tau, prop8_rates
from model import Params, schedule, simulate, speed_caps
from solver import best_response


def caps(*others, A=20.0):
    lo, hi = speed_caps(np.array(others, dtype=float)[:, None], A)
    return lo[0], hi[0]


def test_speed_caps():
    assert caps(-10) == pytest.approx((-10, 30))
    assert caps(0, 0) == pytest.approx((-20, 20))
    assert caps(15) == pytest.approx((-35, 10))
    assert caps(-20 / 3, -20 / 3)[0] == pytest.approx(-20 / 3)


def check_equilibrium(p: Params, rates: np.ndarray) -> list[np.ndarray]:
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
    x = simulate(p, br).x[1]
    assert x[round((liquidation_end(p) - p.t0) / p.dt)] == pytest.approx(0, abs=1e-9)


@pytest.mark.parametrize("I", [3, 9])
def test_prop2_is_a_best_response(I):
    p = Params(I=I, I_d=I // 3, x0=16 / I, x_bar=20 / I)
    rates = equilibrium_rates(p)
    responses = check_equilibrium(p, rates)
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
