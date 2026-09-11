"""Props. 5-6: paper > orderly > distressed liquidation value, and how the
distressed value changes with the number of predators."""

import math

import pytest

from closed_form import equilibrium_rates, orderly_value, paper_value
from model import Params, simulate


def distressed_value(p: Params) -> float:
    """Def. 2 (iii): revenue one distressed trader raises in equilibrium."""
    return simulate(p, equilibrium_rates(p)).cash[0, -1]


@pytest.mark.parametrize("p", [
    Params(),                                     # Prop. 1 example
    Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3),  # Fig. 3, I = 3
    Params(I=9, I_d=3, x0=16 / 9, x_bar=20 / 9),  # Fig. 3, I = 9
])
def test_prop5_ordering(p):
    assert p.x0 >= math.sqrt(p.I_p * (p.I_p - 1)) / (p.I - 1) * p.x_bar
    p_t0 = p.price(p.I * p.x0)
    assert paper_value(p_t0, p.x0) > orderly_value(p, p_t0, p.x0) > distressed_value(p)


def test_prop6_more_predators_raise_distressed_value_but_not_to_orderly():
    # Fixed I_d/I = 1/3, I x_bar = 20, I x0 = 18. Prop. 6 needs
    # x0 >= x_bar sqrt(I_p / I), i.e. 18 >= 20 sqrt(2/3) = 16.33.
    # (The Fig. 3 example, I x0 = 16, does not meet this condition.)
    def total_distressed_value(I):
        p = Params(I=I, I_d=I // 3, x0=18 / I, x_bar=20 / I, dt=0.0005)
        return p.I_d * distressed_value(p)

    values = [total_distressed_value(I) for I in range(3, 31, 3)]
    assert all(a < b for a, b in zip(values, values[1:]))

    # Distressed traders hold I_d x0 = 6 shares in total; price at t0 is p(18).
    p = Params()
    orderly_total = orderly_value(p, p.price(18), 6.0)
    assert total_distressed_value(300) < orderly_total
