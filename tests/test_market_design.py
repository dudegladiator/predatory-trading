"""Props. 8-9: front-running and batch auctions, on the Fig. 3 example with I = 3."""

import numpy as np
import pytest

from closed_form import (
    prop2_rates,
    prop8_price,
    prop8_rates,
    prop9_price,
    prop9_trades,
)
from model import Params, simulate

P = Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3)
T1 = 5.5  # distressed trader starts selling here when front-run


@pytest.fixture(scope="module")
def front_run():
    return simulate(P, prop8_rates(P, T1))


@pytest.fixture(scope="module")
def batch():
    auction, rates = prop9_trades(P)
    return simulate(P, rates, auction)


def test_front_running_matches_eq25(front_run):
    np.testing.assert_allclose(front_run.price, prop8_price(P, T1, front_run.t), atol=1e-9)
    # Predators front-run for tau = 0.4: price 116 -> 108, flat until t1.
    assert front_run.price[front_run.index(5.4)] == pytest.approx(108)
    assert front_run.price[front_run.index(T1)] == pytest.approx(108)
    np.testing.assert_allclose(front_run.x[1:, -1], P.x_bar, atol=1e-9)
    assert front_run.x[0, -1] == pytest.approx(0)


def test_batch_auction_matches_eq26(batch):
    np.testing.assert_allclose(batch.price, prop9_price(P, batch.t), atol=1e-9)
    # Auction clears at 140 - 40 + 20/3 + 16/3 = 112, predators then buy to 113.33.
    assert batch.price[0] == pytest.approx(112)
    np.testing.assert_allclose(batch.x[1:, -1], P.x_bar, atol=1e-9)
    # The distressed trader sells all 16/3 shares at the auction price.
    assert batch.cash[0, -1] == pytest.approx(16 / 3 * 112)


def test_overshoot_ordering(front_run, batch):
    normal = simulate(P, prop2_rates(P))
    assert front_run.overshoot() == pytest.approx(16 / 3)
    assert normal.overshoot() == pytest.approx(10 / 3)
    assert batch.overshoot() == pytest.approx(4 / 3)
    # Front-running lowers the distressed trader's revenue (Prop. 8).
    assert front_run.cash[0, -1] < normal.cash[0, -1]
    # Prop. 9 only claims a smaller overshoot. The distressed trader's revenue is
    # not higher: selling everything at 112 raises 597.33, while selling along
    # the falling-then-recovering path (116 -> 110 -> 113.33) raises 598.22.
    assert batch.cash[0, -1] == pytest.approx(597.333, abs=1e-3)
    assert normal.cash[0, -1] == pytest.approx(598.222, abs=1e-3)


def test_single_predator_skips_the_auction():
    p = Params()
    auction, rates = prop9_trades(p)
    assert auction[1] == 0  # Section VI.B: a single predator does not participate
    assert simulate(p, rates, auction).overshoot() == pytest.approx(p.x_bar - p.x0)


def test_total_speed_never_exceeds_A():
    for rates in (prop8_rates(P, T1), prop9_trades(P)[1]):
        assert np.all(np.abs(rates.sum(axis=0)) <= P.A + 1e-9)


def test_positions_stay_within_limits(front_run, batch):
    for paths in (front_run, batch):
        assert np.all(np.abs(paths.x) <= P.x_bar + 1e-9)


def test_front_running_past_the_position_limit_is_rejected():
    # I = 5 with 3 distressed: eq. (24) would take each predator to -17 < -10.
    # (Front-running lasts tau = 2.6, so t1 and T are pushed out accordingly.)
    p = Params(I=5, I_d=3, x0=9.0, x_bar=10.0, S=60.0, T=11.0)
    with pytest.raises(AssertionError, match="position limit"):
        prop8_rates(p, t1=7.7)
