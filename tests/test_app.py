"""Every app page renders without errors, at the paper's defaults and at inputs
outside the paper's assumptions (which must warn, not crash)."""

import pytest
from streamlit.testing.v1 import AppTest

import app


def render(page: str) -> AppTest:
    def script(page):
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path.cwd()))
        import app

        getattr(app, page)()

    return AppTest.from_function(script, args=(page,), default_timeout=30)


@pytest.mark.parametrize("page", [fn.__name__ for fn, _, _ in app.PAGES])
def test_page_renders_at_defaults(page):
    at = render(page).run()
    assert not at.exception
    assert not at.warning  # the paper's defaults satisfy every assumption


def test_single_predator_shows_paper_numbers():
    at = render("page_single_predator").run()
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Price at t0"] == "116.00"
    assert metrics["Lowest price"] == "100.00"
    assert metrics["Long-run price"] == "110.00"
    assert metrics["Distressed liquidation"] == "864.0"


def test_many_predators_shows_fig3_numbers():
    at = render("page_many_predators").run()
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Lowest price"] == "110.00"
    assert metrics["Overshoot"] == "3.33"


def test_equilibrium_check_shows_no_gain_from_deviating():
    at = render("page_equilibrium_check").run()
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Paper's strategy pays"] == "1214.0000"
    assert metrics["Best possible pays"] == "1214.0000"
    at.select_slider[0].set_value(300).run()
    assert not at.exception


def test_collusion_page_shows_cartel_numbers():
    at = render("page_collusion").run()
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Overshoot"] == "13.33"
    assert metrics["Distressed traders' revenue"] == "576.0"
    assert metrics["Gain from cheating on the cartel"] == "16.67"


def test_contagion_page_scenarios():
    at = render("page_contagion").run()
    assert at.metric[0].value == "0"
    at.selectbox[0].set_value("D and E shocked").run()
    assert at.metric[0].value == "5"
    at.multiselect[0].set_value(["D"]).run()    # bail out D: only E fails
    assert at.metric[0].value == "1"
    at.toggle[0].set_value(False).run()         # sell-or-hold hurdles
    assert not at.exception


def test_unequal_page_matches_formula():
    at = render("page_unequal").run()
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Overshoot, equal positions"] == "3.333"
    assert metrics["Overshoot, spread"] == metrics["Formula λ[A(s − t0) − (X0 − I_p x̄)]"] == "4.833"


def test_unequal_page_with_no_room_to_spread():
    # Found by fuzzing: with x0 = x_bar the spread slider had min = max = 0.
    at = render("page_unequal").run()
    at.slider[2].set_value(10.5)        # total holding I x0
    at.slider[3].set_value(10.5).run()  # total capacity I x_bar, equal to the holding
    assert not at.exception
    assert any("no room" in c.value for c in at.caption)


def test_two_traders_has_no_distressed_slider():
    # Found by fuzzing: with I = 2 the I_d slider had min = max and crashed.
    at = render("page_valuation").run()
    at.slider[0].set_value(2).run()
    assert not at.exception


def test_bad_inputs_warn_instead_of_crashing():
    at = render("page_single_predator").run()
    at.slider[0].set_value(19.0)              # x_bar
    at.slider[2].set_value(3).run()           # 3 distressed: I x_bar = 76 > S
    assert not at.exception
    assert at.warning
