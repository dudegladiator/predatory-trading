# Week 1: Model core and Prop. 1 (single predator)

## What was built
| File | Contents |
|---|---|
| `pyproject.toml`, `uv.lock` | uv project, Python 3.13; numpy, scipy, matplotlib, streamlit; pytest (dev). pytest reads modules from `src/`. |
| `src/model.py` | `Params` (paper's parameters), price eq. (6), `time_grid`, `schedule`, `simulate`, `Paths` |
| `src/closed_form.py` | Prop. 1 strategies (eq. 17) and price path (eq. 18); paper and orderly values (Def. 2) |
| `tests/test_prop1.py` | Checks against the paper's numerical example |
| `figures.py` | Writes `figures/fig1_holdings.png`, `figures/fig2_price.png` |

Commands: `uv run pytest`, `uv run python figures.py`.

## How the simulator works
- Time runs from t0 to T in steps of dt (default 0.001). A strategy is a trading rate per trader per step, an `(I, N)` array.
- Holdings: `x_i(t_{k+1}) = x_i(t_k) + a_i,k · dt`, starting from x0 for every trader.
- Price: `p = μ − λ(S − X)` with X the total holdings of the strategic traders (eq. 6).
- Cash: within a step the price moves linearly, so the cost of a step's trade is `a · dt · (p_k + p_{k+1}) / 2`. That equals the paper's integral of a(t)p(t)dt exactly, so tests can compare exact numbers instead of approximations.
- Payoff (objective 11): `x_i(T) · μ + cash_i(T)`.
- The temporary impact cost G (eq. 8) is not modelled: equilibrium strategies never exceed the speed limit, so it is never paid. Week 5's solver enforces the speed limit as a constraint instead.

## Results (paper's example: S=40, μ=140, λ=1, A=20, x̄=10, x0=8, I=2, t0=5, T=7)
| Check | Paper | Ours |
|---|---|---|
| Price path vs eq. (18) | — | equal at every grid point |
| Price at t = 5, 5.8, 6.3, 7 | 116, 100, 110, 110 | same |
| Holdings | both at 0 at 5.8, predator at 10 by 6.3 | same |
| Predator sells one share less (Fig. 2 dotted line) | loses 101.00 − 100.50 = 0.50 | loses 0.50 |
| Paper > orderly > distressed value | ordering only | 928 > 896 > 864 |

The figures match the paper's Figs. 1–2. Differences: our x-axis starts at t0 = 5 (the paper's starts at 4.5), and the dotted "one share less" line is not drawn (it is tested instead).
