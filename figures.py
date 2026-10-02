"""Reproduce the paper's figures into figures/."""

import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent / "src"))

from closed_form import (  # noqa: E402
    equilibrium_rates,
    orderly_value,
    paper_value,
    prop1_rates,
    prop2_rates,
    prop7_x0,
    prop8_rates,
    prop9_trades,
)
from model import Params, simulate  # noqa: E402
from solver import deviation_gain, fictitious_play, naive_start  # noqa: E402

OUT = Path(__file__).parent / "figures"


def fig1_and_2():
    p = Params()
    paths = simulate(p, prop1_rates(p))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, i, title in [(axes[0], 0, "Panel A: distressed trader"), (axes[1], 1, "Panel B: predator")]:
        ax.plot(paths.t, paths.x[i])
        ax.set(title=title, xlabel="time", ylabel="x(t)", ylim=(0, 10.5))
    fig.suptitle("Figure 1. Holdings with a single predator")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_holdings.png", dpi=150)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(paths.t, paths.price)
    ax.axhline(paths.price[-1], ls=":", c="gray", label="long-run price")
    ax.set(title="Figure 2. Price with a single predator", xlabel="time", ylabel="price")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "fig2_price.png", dpi=150)


def fig3_params(I: int) -> Params:
    """Fig. 3 example: a third of traders distressed, I x0 = 16, I x_bar = 20."""
    return Params(I=I, I_d=I // 3, x0=16 / I, x_bar=20 / I)


def fig3():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for I, style in [(3, "-"), (9, "--"), (27, ":")]:
        p = fig3_params(I)
        paths = simulate(p, prop2_rates(p))
        axes[0].plot(paths.t, paths.x[-1] * I / 3, style, label=f"I={I}")
        axes[1].plot(paths.t, paths.price, style, label=f"I={I}")
    axes[0].set(title="Panel A: each predator's holdings (x I/3)", xlabel="time", ylabel="x(t)")
    axes[1].set(title="Panel B: price", xlabel="time", ylabel="price")
    for ax in axes:
        ax.legend()
    fig.suptitle("Figure 3. Multiple predators")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_multiple_predators.png", dpi=150)


def overshoot_vs_predators():
    """Prop. 3: overshoot shrinks as predators grow, total capacity fixed."""
    Is = range(3, 91, 3)
    overshoots = []
    for I in Is:
        p = fig3_params(I)
        overshoots.append(simulate(p, prop2_rates(p)).overshoot())
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([I * 2 // 3 for I in Is], overshoots, "o-")
    ax.set(title="Prop. 3: overshoot vs number of predators",
           xlabel="number of predators $I_p$", ylabel="price overshoot")
    fig.tight_layout()
    fig.savefig(OUT / "prop3_overshoot.png", dpi=150)


def valuation_vs_predators():
    """Props. 5-6: total value of the distressed traders' shares (I x0 = 18)."""
    Is = range(3, 61, 3)
    distressed = []
    for I in Is:
        p = Params(I=I, I_d=I // 3, x0=18 / I, x_bar=20 / I)
        distressed.append(p.I_d * simulate(p, equilibrium_rates(p)).cash[0, -1])
    p = Params(x0=6.0)
    p_t0 = p.price(18)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axhline(paper_value(p_t0, 6.0), ls="--", c="gray", label="paper value")
    ax.axhline(orderly_value(p, p_t0, 6.0), ls=":", c="black", label="orderly liquidation")
    ax.plot([I * 2 // 3 for I in Is], distressed, "o-", label="distressed liquidation")
    ax.set(title="Props. 5-6: value of the distressed position",
           xlabel="number of predators $I_p$", ylabel="value")
    ax.legend(loc="center right")
    fig.tight_layout()
    fig.savefig(OUT / "prop56_valuation.png", dpi=150)


def disclosure():
    """Prop. 7: position built before t0, with and without disclosure (I = 5)."""
    pis = [i / 100 for i in range(101)]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(pis, [prop7_x0(5, 10, pi, disclosed=False) for pi in pis], label="not disclosed")
    ax.plot(pis, [prop7_x0(5, 10, pi, disclosed=True) for pi in pis], "--", label="disclosed")
    ax.axhline(3 / 4 * 10, ls=":", c="gray", label="predation threshold")
    ax.set(title="Prop. 7: initial position x(t0), I = 5, x_bar = 10",
           xlabel="probability of distress pi", ylabel="x(t0)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "prop7_disclosure.png", dpi=150)


def market_design():
    """Props. 2, 8, 9 on the Fig. 3 example with I = 3."""
    p = Params(I=3, I_d=1, x0=16 / 3, x_bar=20 / 3)
    auction, rates = prop9_trades(p)
    cases = [
        ("front-running (distressed start at 5.5)", simulate(p, prop8_rates(p, 5.5)), "-"),
        ("normal (Prop. 2)", simulate(p, prop2_rates(p)), "--"),
        ("batch auction at t0", simulate(p, rates, auction), ":"),
    ]
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, paths, style in cases:
        ax.plot(paths.t, paths.price, style,
                label=f"{label}: overshoot {paths.overshoot():.2f}, revenue {paths.cash[0, -1]:.1f}")
    ax.set(title="Props. 8-9: market design, I = 3", xlabel="time", ylabel="price")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "prop89_market_design.png", dpi=150)


def fictitious_play_convergence():
    """Week 6: predators learn the Prop. 2 equilibrium from a naive start (I = 3)."""
    p = fig3_params(3)
    start = naive_start(p, equilibrium_rates(p)[: p.I_d])
    rounds = (1, 2, 5, 10, 20, 50, 100, 200, 300)
    history = {0: start, **fictitious_play(p, start, rounds[-1], record=rounds)}
    eq = simulate(p, prop2_rates(p))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for k, style in [(0, ":"), (10, "-."), (50, "--"), (300, "-")]:
        axes[0].plot(eq.t, simulate(p, history[k]).price, style, label=f"round {k}")
    axes[0].plot(eq.t, eq.price, c="black", lw=2, alpha=0.3, label="paper (eq. 20)")
    axes[0].set(title="Panel A: price path", xlabel="time", ylabel="price")
    axes[0].legend()
    gains = [deviation_gain(p, history[k]) for k in rounds]
    axes[1].loglog(rounds, gains, "o-")
    axes[1].set(title="Panel B: gain from deviating", xlabel="round", ylabel="gain")
    fig.suptitle("Fictitious play converges to the paper's equilibrium (I = 3)")
    fig.tight_layout()
    fig.savefig(OUT / "fictitious_play.png", dpi=150)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig1_and_2()
    fig3()
    overshoot_vs_predators()
    valuation_vs_predators()
    disclosure()
    market_design()
    fictitious_play_convergence()
