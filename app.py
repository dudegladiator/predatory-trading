"""Interactive replication of Brunnermeier & Pedersen (2005), "Predatory Trading".

Run with: uv run streamlit run app.py
"""

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from closed_form import (  # noqa: E402
    collusion_rates,
    equilibrium_rates,
    orderly_value,
    paper_value,
    preys,
    prop7_x0,
    prop8_rates,
    prop9_trades,
)
from contagion import cascade, equilibria, hurdles  # noqa: E402
from model import Params, simulate  # noqa: E402
from plots import NAMES, wealth_figure  # noqa: E402
from solver import best_response, deviation_gain, fictitious_play, naive_start  # noqa: E402

PRESETS = {
    "Prop. 1 example (1 predator)": Params(),
    "Fig. 3, I = 3 (2 predators)": Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3),
    "Fig. 3, I = 9 (6 predators)": Params(I=9, I_d=3, x0=16 / 9, x_bar=20 / 9),
}
LEARNING_ROUNDS = (1, 2, 5, 10, 20, 50, 100, 200, 300)

CONTAGION = Params(I=6, x_bar=6.0, x0=5.0, T=9.0, dt=0.005)
W_LOW = 100.0
CALM = [115.0, 140.0, 155.0, 200.0, 200.0, 200.0]
SCENARIOS = {
    "No shock (Fig. 4, Panel A)": CALM,
    "D shocked (Fig. 4, Panel B)": [115.0, 140.0, 155.0, 90.0, 200.0, 200.0],
    "D and E shocked": [115.0, 140.0, 155.0, 90.0, 90.0, 200.0],
}
def market() -> Params:
    """Market parameters shared by every page, set in the sidebar."""
    with st.sidebar:
        st.header("Market")
        lam = st.slider("Price impact λ", 0.2, 3.0, 1.0, 0.1)
        A = st.slider("Speed limit A (shares per unit time)", 5.0, 40.0, 20.0, 1.0)
        T = st.slider("Horizon T", 7.0, 12.0, 7.0, 0.5)
        st.caption("Fixed: S = 40, μ = 140, t0 = 5.")
    return Params(lam=lam, A=A, T=T)


def attempt(fn, *args):
    """Run a model function; inputs outside the paper's assumptions get a warning."""
    try:
        return fn(*args)
    except AssertionError as e:
        st.warning(f"Outside the paper's assumptions: {e or 'condition of the proposition not met'}")
        return None


def chart(t, series: dict, y_label: str):
    st.line_chart(pd.DataFrame(series, index=pd.Index(t, name="time")), x_label="time", y_label=y_label)


def traders(p: Params, key: str, I_default: int, I_d_default: int,
            total_x0: float, total_x_bar: float) -> Params:
    """Sliders for the number of traders and their (total) holdings."""
    c1, c2, c3, c4 = st.columns(4)
    I = c1.slider("Strategic traders I", 2, 60, I_default, key=f"{key}I")
    if I > 2:
        I_d = c2.slider("Distressed I_d", 1, I - 1, min(I_d_default, I - 1), key=f"{key}Id")
    else:  # a slider needs min < max
        I_d = 1
        c2.markdown("Distressed I_d: **1**")
    X_bar = c4.slider("Total capacity I·x̄", 2.0, 39.0, total_x_bar, 0.5, key=f"{key}xb")
    X0 = c3.slider("Total holding I·x(t0)", 1.0, X_bar, min(total_x0, X_bar), 0.5, key=f"{key}x0")
    return replace(p, I=I, I_d=I_d, x0=X0 / I, x_bar=X_bar / I)


def scaled(p: Params, k: int) -> Params:
    """k times as many traders with the same totals (Prop. 3's comparison)."""
    return replace(p, I=k * p.I, I_d=k * p.I_d, x0=p.x0 / k, x_bar=p.x_bar / k)


def page_model():
    st.title("Predatory Trading")
    st.caption("Brunnermeier & Pedersen (2005), Journal of Finance 60(4)")
    st.markdown("""
When a large trader is **forced to sell** and rivals know it, the rivals do not provide
liquidity. They **sell alongside it and buy back afterwards**. The price falls further
than the forced selling alone would push it (**overshooting**), and the distressed
trader's extra loss is the predators' profit.

**Model**
- One risky asset, supply S, expected final value μ.
- Long-term investors: downward-sloping demand, so the price is linear in what the
  strategic traders hold, X:""")
    st.latex(r"p(t) = \mu - \lambda\,(S - X(t))")
    st.markdown("""
- I strategic traders, each limited to |xᵢ| ≤ x̄. Together they can trade at most
  **A shares per unit time** without extra impact costs.
- At t0, I_d of them become distressed and must sell at speed A/I until they hold
  nothing. The other I_p = I − I_d are the predators.

**Lemma 1.** A predator's problem reduces to""")
    st.latex(r"\min_{a_i} \int_0^T a_i(t)\, X_{-i}(t)\, dt \quad \text{s.t. } x_i(T) = \bar{x}")
    st.markdown("""
It profits from how **other traders' holdings X₋ᵢ** move the price, not from its own
impact. That separates predation from manipulation: the predator sells while X₋ᵢ is
falling and buys once it stops.

**Pages**
1. Single predator (Prop. 1, Figs. 1–2)
2. Many predators (Props. 2, 2′, 3, Fig. 3)
3. Valuation & disclosure (Props. 5–7)
4. Market design: front-running and batch auctions (Props. 8–9)
5. Equilibrium check: a linear-programming solver and fictitious play confirm the paper
6. Collusion vs competition (extension F)
7. Contagion and bailouts (extension C)
8. Predators with unequal positions (stretch A)
""")


def page_single_predator():
    st.title("Single predator (Prop. 1)")
    p = market()
    c1, c2, c3 = st.columns(3)
    x_bar = c1.slider("Capacity x̄", 2.0, 19.0, 10.0, 0.5)
    x0 = c2.slider("Holding at t0, x(t0)", 0.5, x_bar, min(8.0, x_bar), 0.5)
    I_d = c3.slider("Distressed traders", 1, 3, 1)
    p = replace(p, I=I_d + 1, I_d=I_d, x0=x0, x_bar=x_bar)

    rates = attempt(equilibrium_rates, p)
    if rates is None:
        return
    paths = simulate(p, rates)
    p_t0 = paths.start_price

    m = st.columns(4)
    m[0].metric("Price at t0", f"{p_t0:.2f}")
    m[1].metric("Lowest price", f"{paths.price.min():.2f}")
    m[2].metric("Long-run price", f"{paths.price[-1]:.2f}")
    m[3].metric("Overshoot", f"{paths.overshoot():.2f}")

    left, right = st.columns(2)
    with left:
        st.subheader("Holdings")
        chart(paths.t, {"distressed": paths.x[0], "predator": paths.x[-1]}, "x(t)")
    with right:
        st.subheader("Price")
        chart(paths.t, {"price": paths.price}, "price")

    st.subheader("What the distressed trader's position is worth (Def. 2)")
    v = st.columns(3)
    v[0].metric("Paper value x·p(t0)", f"{paper_value(p_t0, x0):.1f}")
    v[1].metric("Orderly (secret) liquidation", f"{orderly_value(p, p_t0, x0):.1f}")
    v[2].metric("Distressed liquidation", f"{paths.cash[0, -1]:.1f}")
    st.caption("The predator sells while the distressed trader sells, then buys back below "
               "the long-run price. With the paper's values the price goes 116 → 100 → 110.")


def page_many_predators():
    st.title("Many predators (Props. 2, 2′, 3)")
    p = traders(market(), "many", 3, 1, 16.0, 20.0)
    regime = "predation (Prop. 2)" if preys(p) else "no predation: predators buy at once (Prop. 2′)"
    st.info(f"I_p = {p.I_p} predator(s), x(t0) = {p.x0:.2f}, x̄ = {p.x_bar:.2f} → **{regime}**")

    rates = attempt(equilibrium_rates, p)
    if rates is None:
        return
    paths = simulate(p, rates)
    m = st.columns(3)
    m[0].metric("Lowest price", f"{paths.price.min():.2f}")
    m[1].metric("Long-run price", f"{paths.price[-1]:.2f}")
    m[2].metric("Overshoot", f"{paths.overshoot():.2f}")

    left, right = st.columns(2)
    with left:
        st.subheader("Holdings")
        chart(paths.t, {"each distressed": paths.x[0], "each predator": paths.x[-1]}, "x(t)")
    with right:
        st.subheader("Price")
        chart(paths.t, {"price": paths.price}, "price")

    st.subheader("More predators, same totals (Prop. 3)")
    rows = []
    for k in range(1, 21):
        q = scaled(p, k)
        try:
            rows.append((q.I_p, simulate(q, equilibrium_rates(q)).overshoot()))
        except AssertionError:
            break
    df = pd.DataFrame(rows, columns=["predators", "overshoot"]).set_index("predators")
    st.line_chart(df, x_label="number of predators I_p", y_label="overshoot")
    st.caption("Predators compete to rebuild their positions first, so with more of them "
               "the buying starts earlier and the overshoot shrinks toward 0.")


def page_valuation():
    st.title("Valuation & disclosure (Props. 5–7)")
    p = market()

    st.subheader("Value of the distressed position vs number of predators")
    p = traders(p, "val", 3, 1, 18.0, 20.0)
    rows = []
    for k in range(1, 21):
        q = scaled(p, k)
        try:
            value = q.I_d * simulate(q, equilibrium_rates(q)).cash[0, -1]
        except AssertionError:
            break
        rows.append((q.I_p, value))
    if not rows:
        attempt(equilibrium_rates, p)  # shows why
        return
    X_d = p.I_d * p.x0  # shares held by all distressed traders
    p_t0 = p.price(p.I * p.x0)
    df = pd.DataFrame(rows, columns=["predators", "distressed liquidation"]).set_index("predators")
    df["orderly liquidation"] = orderly_value(p, p_t0, X_d)
    df["paper value"] = paper_value(p_t0, X_d)
    st.line_chart(df, x_label="number of predators I_p", y_label="value")
    st.caption("Paper > orderly > distressed. More predators help the distressed traders, "
               "but even many predators leave them below the orderly value (Prop. 6).")

    st.subheader("Disclosure and the initial position (Prop. 7)")
    c1, c2 = st.columns(2)
    I = c1.slider("Strategic traders I", 2, 20, 5, key="discI")
    pi = c2.slider("Probability of distress π", 0.0, 1.0, 0.5, 0.05)
    x_bar = 10.0
    grid = [i / 50 for i in range(51)]
    df = pd.DataFrame({
        "not disclosed": [prop7_x0(I, x_bar, q, disclosed=False) for q in grid],
        "disclosed": [prop7_x0(I, x_bar, q, disclosed=True) for q in grid],
        "predation threshold": (I - 2) / (I - 1) * x_bar,
    }, index=pd.Index(grid, name="π"))
    st.line_chart(df, x_label="probability of distress π", y_label="x(t0), x̄ = 10")
    m = st.columns(2)
    m[0].metric("x(t0) not disclosed", f"{prop7_x0(I, x_bar, pi, disclosed=False):.2f}")
    m[1].metric("x(t0) disclosed", f"{prop7_x0(I, x_bar, pi, disclosed=True):.2f}")
    st.caption("Disclosure makes traders hold less, but never little enough to stop predation.")


def page_market_design():
    st.title("Market design: front-running & batch auctions (Props. 8–9)")
    p = traders(market(), "mkt", 3, 1, 16.0, 20.0)
    end = p.t0 + p.x0 / (p.A / p.I)
    t1 = st.slider("Front-running: distressed traders start selling at t1", p.t0, p.T, 5.5, 0.05)

    cases = {}
    rates = attempt(equilibrium_rates, p)
    if rates is not None:
        cases["normal"] = simulate(p, rates)
    rates = attempt(prop8_rates, p, t1)
    if rates is not None:
        cases["front-running"] = simulate(p, rates)
    trades = attempt(prop9_trades, p)
    if trades is not None:
        cases["batch auction"] = simulate(p, trades[1], trades[0])
    if not cases:
        return

    t = next(iter(cases.values())).t
    chart(t, {name: paths.price for name, paths in cases.items()}, "price")
    st.dataframe(pd.DataFrame({
        "overshoot": {name: paths.overshoot() for name, paths in cases.items()},
        "distressed revenue": {name: paths.cash[0, -1] for name, paths in cases.items()},
    }).round(2))
    st.caption(f"Without front-running the distressed traders sell from t0 to {end:.2f}. "
               "A batch auction reduces the overshoot, since predators can no longer sell down "
               "the demand curve first, but the distressed seller's revenue is not higher: "
               "everything sells at one price.")

def learning(preset: str) -> tuple[dict, dict]:
    """Price path and deviation gain after each recorded round, from round 0."""
    p = PRESETS[preset]
    start = naive_start(p, equilibrium_rates(p)[: p.I_d])
    history = {0: start, **fictitious_play(p, start, LEARNING_ROUNDS[-1], record=LEARNING_ROUNDS)}
    prices = {k: simulate(p, r).price for k, r in history.items()}
    gains = {k: deviation_gain(p, r) for k, r in history.items()}
    return prices, gains

def page_equilibrium_check():
    st.title("Checking the equilibrium (Lemma 1 as a linear program)")
    st.markdown("""
Hold every other trader at the paper's strategy and ask a computer for one predator's
**best possible strategy**. By Lemma 1 its payoff is linear in its own trades, so this
is a linear program with an exact answer. If the paper is right, nothing beats the
paper's strategy. The parameters here are the paper's own.""")
    preset = st.selectbox("Example", list(PRESETS))
    p = PRESETS[preset]
    rates = equilibrium_rates(p)
    i = p.I - 1
    br = best_response(p, rates, i, p.x_bar)
    paper, best = simulate(p, rates), simulate(p, br)
    m = st.columns(3)
    m[0].metric("Paper's strategy pays", f"{paper.payoff(p.mu)[i]:.4f}")
    m[1].metric("Best possible pays", f"{best.payoff(p.mu)[i]:.4f}")
    m[2].metric("Gain from deviating", f"{best.payoff(p.mu)[i] - paper.payoff(p.mu)[i]:.6f}")
    chart(paper.t, {"paper's strategy": paper.x[i], "LP best response": best.x[i]}, "predator's holdings")
    st.caption("The two can differ after the selling ends (footnote 13: buy-back speed is free) "
               "but pay the same.")

    st.subheader("Learning the equilibrium from scratch")
    st.markdown("""
Start the predators on a **naive** strategy: just buy steadily while the distressed
trader sells. Each round they move a step 1/(k + 2) toward their best response to each
other (**fictitious play**). Undamped best responses cycle, because they are all-or-nothing.""")
    learn = st.selectbox("Example", list(PRESETS)[1:], key="learn")
    prices, gains = learning(learn)
    q = PRESETS[learn]
    k = st.select_slider("Round", options=[0, *LEARNING_ROUNDS], value=0)
    eq = simulate(q, equilibrium_rates(q))
    left, right = st.columns(2)
    with left:
        chart(eq.t, {f"round {k}": prices[k], "paper (eq. 20)": eq.price}, "price")
    with right:
        df = pd.DataFrame({"gain from deviating": gains}).rename_axis("round")
        st.line_chart(df.iloc[1:], x_label="round", y_label="gain from deviating")
    st.caption(f"Round {k}: a predator could still gain {gains[k]:.3f} by deviating. "
               "The gap shrinks toward 0 as the price path converges to the paper's.")


def page_collusion():
    st.title("Extension F: collusion vs competition")
    st.markdown("""
Competing predators race to rebuild their positions first, which limits predation
(Prop. 3). A **cartel** maximises the predators' *joint* profit instead: it acts like one
predator with their combined capacity, selling until the distressed traders are out and
only then rebuilding. Checked with a joint linear program (week 7).""")
    p = traders(market(), "col", 3, 1, 16.0, 20.0)
    comp_rates = attempt(equilibrium_rates, p)
    cart_rates = attempt(collusion_rates, p)
    if comp_rates is None or cart_rates is None:
        return
    comp, cart = simulate(p, comp_rates), simulate(p, cart_rates)

    m = st.columns(4)
    m[0].metric("Overshoot", f"{cart.overshoot():.2f}", f"{cart.overshoot() - comp.overshoot():+.2f} vs competing",
                delta_color="inverse")
    m[1].metric("Distressed traders' revenue", f"{p.I_d * cart.cash[0, -1]:.1f}",
                f"{p.I_d * (cart.cash[0, -1] - comp.cash[0, -1]):+.1f}")
    m[2].metric("Predators' joint payoff", f"{cart.payoff(p.mu)[p.I_d:].sum():.1f}",
                f"{(cart.payoff(p.mu) - comp.payoff(p.mu))[p.I_d:].sum():+.1f}")
    if p.I_p >= 2:
        i = p.I - 1
        cheat = simulate(p, best_response(p, cart_rates, i, p.x_bar)).payoff(p.mu)[i] - cart.payoff(p.mu)[i]
        m[3].metric("Gain from cheating on the cartel", f"{cheat:.2f}")
    chart(comp.t, {"competing": comp.price, "cartel": cart.price}, "price")
    st.caption("Collusion is a pure transfer: the predators gain exactly what the distressed "
               "traders lose. But each member gains by cheating (rebuilding early), so the cartel "
               "is not an equilibrium. The paper notes tacit collusion cannot occur in this model.")

    st.subheader("More predators, same totals")
    rows = []
    for k in range(1, 21):
        q = scaled(p, k)
        try:
            c, d = simulate(q, equilibrium_rates(q)), simulate(q, collusion_rates(q))
        except AssertionError:
            break
        rows.append((q.I_p, c.overshoot(), d.overshoot()))
    df = pd.DataFrame(rows, columns=["predators", "competing", "cartel"]).set_index("predators")
    st.line_chart(df, x_label="number of predators I_p", y_label="overshoot")
    st.caption("Competition erodes the overshoot as predators are added; a cartel keeps it "
               "whatever its size.")

def contagion_hurdles(can_buy: bool) -> np.ndarray:
    return hurdles(CONTAGION, can_buy)


def page_contagion():
    st.title("Extension C: contagion and bailouts")
    st.markdown(f"""
Six traders A–F (Section III.B, Fig. 4). A trader must liquidate if its wealth falls to
W̲ = {W_LOW:.0f}. **W(I_d)** is the wealth below which a trader cannot avoid distress if the
market expects I_d traders to fail: the more failures expected, the fiercer the predation
and the higher the hurdle (Prop. 4). Each hurdle is computed by finding the trader's
best survival strategy, an optimisation over all strategies (eq. 21).""")
    c1, c2 = st.columns(2)
    scenario = c1.selectbox("Scenario", list(SCENARIOS))
    can_buy = c2.toggle("Survival strategies may buy (eq. 21 literally)", value=True,
                        help="Off: a trader in trouble may only sell or hold.")
    D = contagion_hurdles(can_buy)
    cols = st.columns(6)
    wealth = np.array([cols[i].slider(NAMES[i], 60.0, 220.0, SCENARIOS[scenario][i], 1.0,
                                      key=f"w{i}{scenario}") for i in range(6)])
    rescued = st.multiselect("Central bank bails out (recapitalises above every hurdle)",
                             list(NAMES[:6]), key=f"bail{scenario}")
    for name in rescued:
        wealth[NAMES.index(name)] = max(wealth[NAMES.index(name)], W_LOW + D[-1] + 1)

    steps = cascade(wealth, W_LOW, D)
    failed = steps[-1]
    left, right = st.columns([3, 2])
    with left:
        st.pyplot(wealth_figure(wealth, W_LOW, D, failed, "Wealth vs survival hurdles (red = fails)"))
    with right:
        st.metric("Traders who fail (ripple from the shocked)", len(failed))
        st.markdown("**Ripple:** " + " → ".join(", ".join(NAMES[i] for i in step) or "none"
                                               for step in steps))
        eq = equilibria(wealth, W_LOW, D)
        st.markdown(f"**All consistent outcomes** (number of failures): {eq}")
        if len(eq) > 1:
            st.caption("Several outcomes are self-fulfilling: if the market expects more "
                       "failures, predation is fiercer and they happen (panic).")
        st.dataframe(pd.DataFrame({"W(I_d)": W_LOW + D[1:]}, index=pd.Index(range(1, 7), name="I_d")).round(2))
    if failed:
        p = replace(CONTAGION, I_d=len(failed))
        rates = attempt(equilibrium_rates, p) if p.I_d < p.I else None
        if rates is not None:
            paths = simulate(p, rates)
            chart(paths.t, {f"price with {len(failed)} failing": paths.price}, "price")

PAGES = [
    (page_model, "The model", "model"),
    (page_single_predator, "Single predator", "single"),
    (page_many_predators, "Many predators", "many"),
    (page_valuation, "Valuation & disclosure", "valuation"),
    (page_market_design, "Market design", "market-design"),
    (page_equilibrium_check, "Equilibrium check", "equilibrium"),
    (page_collusion, "Collusion", "collusion"),
    (page_contagion, "Contagion", "contagion"),
]

if __name__ == "__main__":
    st.navigation([st.Page(fn, title=title, url_path=path, default=fn is page_model)
                   for fn, title, path in PAGES]).run()
