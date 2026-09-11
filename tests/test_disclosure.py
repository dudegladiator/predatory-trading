"""Prop. 7: positions built before t0, with and without disclosure."""

import pytest

from closed_form import preys, prop7_x0
from model import Params


def test_prop7_formulas():
    assert prop7_x0(I=5, x_bar=10, pi=0.5, disclosed=False) == pytest.approx(9.0)
    assert prop7_x0(I=5, x_bar=10, pi=0.5, disclosed=True) == pytest.approx(8.75)
    assert prop7_x0(I=2, x_bar=10, pi=0.5, disclosed=False) == pytest.approx(5.0)


@pytest.mark.parametrize("I", [3, 5, 10])
@pytest.mark.parametrize("pi", [0.1, 0.5, 0.9])
def test_disclosure_shrinks_positions_but_predation_still_happens(I, pi):
    no_disclosure = prop7_x0(I, 10, pi, disclosed=False)
    disclosure = prop7_x0(I, 10, pi, disclosed=True)
    assert disclosure < no_disclosure
    # Prop. 7: either way x(t0) is large enough that predators prey (Prop. 2).
    for x0 in (no_disclosure, disclosure):
        assert preys(Params(I=I, I_d=1, x0=x0, x_bar=10))
