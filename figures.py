"""Reproduce the paper's figures into figures/."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent / "src"))

from closed_form import prop1_rates  # noqa: E402
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


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig1_and_2()
