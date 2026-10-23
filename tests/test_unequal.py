"""Week 9, stretch A: predators with unequal positions (footnote 15).

Footnote 15 is only described in words; the LP solver checks it is an
equilibrium. Grids are chosen so the switch time s falls on a grid point, which
makes the check exact. Off the grid the step containing s is averaged and the
gain from deviating is about 4e-5 at dt = 0.001.
"""

from dataclasses import replace

import numpy as np
import pytest

from closed_form import prop2_rates
from model import Params, simulate
from solver import deviation_gain
from unequal import footnote15_rates, predicted_overshoot, switch_time

I3 = Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3)   # Fig. 3 totals
I4 = Params(I=4, I_d=1, x0=4.0, x_bar=5.0)


def spread(p: Params, offsets) -> Params:
    """Predators at x0 + offsets (summing to 0), distressed at x0."""
    return replace(p, holdings=tuple([p.x0] * p.I_d + [p.x0 + o for o in offsets]))


@pytest.mark.parametrize("p", [I3, Params(I=9, I_d=3, x0=16 / 9, x_bar=20 / 9)])
def test_equal_positions_reduce_to_prop2(p):
    np.testing.assert_allclose(footnote15_rates(spread(p, [0] * p.I_p)), prop2_rates(p), atol=1e-9)


@pytest.mark.parametrize("p", [
    replace(spread(I3, [-0.5, 0.5]), dt=0.0005),
    spread(I3, [-1.0, 1.0]),
    spread(I4, [-0.4, 0.0, 0.4]),
    replace(spread(I4, [-0.8, 0.0, 0.8]), dt=1 / 7500),
])
def test_footnote15_is_an_equilibrium(p):
    assert abs(deviation_gain(p, footnote15_rates(p))) < 1e-6
    paths = simulate(p, footnote15_rates(p))
    np.testing.assert_allclose(paths.x[:, -1], [0] * p.I_d + [p.x_bar] * p.I_p, atol=1e-9)


def test_overshoot_rises_with_dispersion():
    # Footnote 15's claim, I = 3: 3.33 -> 4.08 -> 4.83 as the predators spread out.
    values = [simulate(p, footnote15_rates(p)).overshoot()
              for p in (replace(spread(I3, [-d, d]), dt=0.0005) for d in (0.0, 0.5, 1.0))]
    np.testing.assert_allclose(values, [10 / 3, 10 / 3 + 0.75, 10 / 3 + 1.5], atol=1e-9)


@pytest.mark.parametrize("offsets", [[-0.8, 0.0, 0.8], [-0.8, 0.4, 0.4]])
def test_only_the_smallest_position_matters(offsets):
    # Same smallest predator (3.2) and same total, different spread: same
    # overshoot, 2.7333, as the derived formula says.
    p = replace(spread(I4, offsets), dt=1 / 7500)
    assert simulate(p, footnote15_rates(p)).overshoot() == pytest.approx(predicted_overshoot(p), abs=1e-9)
    assert predicted_overshoot(p) == pytest.approx(41 / 15)
    assert abs(deviation_gain(p, footnote15_rates(p))) < 1e-6


def test_switch_time_is_set_by_the_smallest_predator():
    assert switch_time(I3) == pytest.approx(5.3)                       # Prop. 2's t0 + tau
    assert switch_time(spread(I3, [-1.0, 1.0])) == pytest.approx(5.375)


def test_positions_above_the_limit_are_rejected():
    with pytest.raises(AssertionError, match="within the limit"):
        footnote15_rates(spread(I3, [-1.5, 1.5]))  # 6.83 > x_bar = 6.67
