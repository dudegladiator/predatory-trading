"""Reproduce the paper's figures into figures/."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent / "src"))

from closed_form import prop1_rates, prop2_rates  # noqa: E402
from model import Params, simulate  # noqa: E402

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


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig1_and_2()
    fig3()
    overshoot_vs_predators()
