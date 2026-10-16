"""Charts shared by figures.py and the app."""

import numpy as np
from matplotlib.figure import Figure

NAMES = "ABCDEFGHIJ"


def wealth_vs_hurdles(ax, wealth: np.ndarray, W_low: float, D: np.ndarray,
                      failed: list[int], title: str) -> None:
    """Fig. 4 style: each trader's wealth against the survival hurdles W(I_d)."""
    names = list(NAMES[: len(wealth)])
    colors = ["tab:red" if i in failed else "tab:blue" for i in range(len(wealth))]
    ax.bar(names, wealth, color=colors)
    # One line per distinct level; equal hurdles share a label, e.g. "W(5)=W(6)".
    levels: dict[float, list[int]] = {}
    for k in range(1, len(D)):
        levels.setdefault(round(W_low + D[k], 6), []).append(k)
    for level, ks in levels.items():
        ax.axhline(level, ls=":", c="gray", lw=1)
        ax.text(1.01, level, "=".join(f"W({k})" for k in ks), transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=8, color="gray")
    ax.axhline(W_low, c="black", lw=1)
    ax.set(title=title, ylabel="wealth at t0", ylim=(min(W_low, wealth.min()) - 20, max(wealth.max(), W_low + D[-1]) + 15))


def wealth_figure(wealth, W_low, D, failed, title) -> Figure:
    fig = Figure(figsize=(6, 4))
    wealth_vs_hurdles(fig.subplots(), wealth, W_low, D, failed, title)
    fig.tight_layout()
    return fig
