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

def test_bad_inputs_warn_instead_of_crashing():
    at = render("page_single_predator").run()
    at.slider[0].set_value(19.0)              # x_bar
    at.slider[2].set_value(3).run()           # 3 distressed: I x_bar = 76 > S
    assert not at.exception
    assert at.warning
