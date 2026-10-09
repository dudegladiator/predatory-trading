"""Week 7, extension F: collusive vs competitive predators (Fig. 3 totals:
a third of traders distressed, I x0 = 16, I x_bar = 20)."""

import numpy as np
import pytest

from closed_form import collusion_rates, equilibrium_rates
from model import Params, impact_costs, simulate
from solver import collusive_response, deviation_gain


def fig3(I: int) -> Params:
    return Params(I=I, I_d=I // 3, x0=16 / I, x_bar=20 / I)


def predators_total(p: Params, rates: np.ndarray) -> float:
    return simulate(p, rates).payoff(p.mu)[p.I_d:].sum()


@pytest.mark.parametrize("I", [3, 9])
def test_closed_form_cartel_is_the_joint_optimum(I):
    p = fig3(I)
    cartel = collusion_rates(p)
    lp = collusive_response(p, cartel)
    assert predators_total(p, lp) == pytest.approx(predators_total(p, cartel), abs=1e-6)
    assert np.all(impact_costs(p, cartel) == 0)


def test_one_predator_cartel_is_prop1():
    p = Params()
    np.testing.assert_allclose(collusion_rates(p), equilibrium_rates(p))


@pytest.mark.parametrize("I", [3, 9, 27])
def test_collusion_vs_competition(I):
    p = fig3(I)
    comp, cart = simulate(p, equilibrium_rates(p)), simulate(p, collusion_rates(p))
    # The cartel sells everything before rebuilding: the price falls to
    # mu - lam S = 100, so the overshoot is lam I_p x_bar = 13.33 for any I.
    assert cart.price.min() == pytest.approx(100)
    assert cart.overshoot() == pytest.approx(40 / 3)
    assert cart.overshoot() > comp.overshoot()
    # Collusion moves money from the distressed traders to the predators.
    assert cart.cash[0, -1] < comp.cash[0, -1]
    assert predators_total(p, collusion_rates(p)) > predators_total(p, equilibrium_rates(p))


@pytest.mark.parametrize("I", [3, 9])
def test_cartel_members_gain_by_cheating(I):
    # Collusion is not an equilibrium: one member profits by rebuilding early.
    # Matches the paper: tacit collusion cannot occur in this model.
    p = fig3(I)
    assert deviation_gain(p, collusion_rates(p)) > 1


@pytest.mark.parametrize("I", [3, 9, 27])
def test_collusion_is_a_pure_transfer_from_the_distressed(I):
    # Long-term investors are unaffected (Section III.A): whatever the cartel
    # gains over competition, the distressed traders lose.
    p = fig3(I)
    comp, cart = simulate(p, equilibrium_rates(p)), simulate(p, collusion_rates(p))
    distressed_loss = p.I_d * (comp.cash[0, -1] - cart.cash[0, -1])
    predator_gain = predators_total(p, collusion_rates(p)) - predators_total(p, equilibrium_rates(p))
    assert predator_gain == pytest.approx(distressed_loss, abs=1e-6)


@pytest.mark.parametrize("p", [fig3(3), fig3(9), Params(I=3, I_d=1, x0=4.0, x_bar=10.0)])
def test_cartel_lp_never_breaks_the_speed_limit(p):
    # The joint LP caps the group's total; splitting it equally must keep every
    # member within its own equal-priority cap.
    assert impact_costs(p, collusive_response(p, collusion_rates(p))).sum() == 0


def test_cartel_preys_even_where_competitors_would_provide_liquidity():
    # x0 = 4 < (I_p - 1)/(I - 1) x_bar = 5: competing predators buy at once
    # (Prop. 2', no overshoot), but a cartel still sells first and preys.
    p = Params(I=3, I_d=1, x0=4.0, x_bar=10.0)
    cartel = collusion_rates(p)
    assert predators_total(p, collusive_response(p, cartel)) == pytest.approx(
        predators_total(p, cartel), abs=1e-6)
    assert simulate(p, equilibrium_rates(p)).overshoot() == pytest.approx(0)
    assert simulate(p, cartel).overshoot() == pytest.approx(12)  # 112 -> 100 -> 120
