# Predatory Trading: replication and extensions

A discrete-time implementation of Brunnermeier & Pedersen (2005), "Predatory Trading", *Journal of Finance* 60(4), with an independent numerical check of its equilibria and three extensions. The paper is available from the authors at https://w4.stern.nyu.edu/facdir/lpederse/papers/predatory_trading.pdf; save it as `predatory_trading.pdf` in the project root to follow the equation and page references.

## Run it

Demo - https://predatory-trading.streamlit.app/
This can take time, as this is deployed on 3rd party service; kindly wake up the app and wait for 5 minutes. Thanks


Requires [uv](https://docs.astral.sh/uv/). It installs Python 3.13 and the dependencies on first use.

```
uv run streamlit run app.py   # interactive app, one page per result
uv run pytest                 # 115 tests (about 30 s)
uv run python figures.py      # writes the report figures to figures/
cd slides && latexmk -pdf slides.tex   # the presentation (needs a TeX distribution)
cd report && latexmk -pdf report.tex   # the report
```

## What is where
| Path | Contents |
|---|---|
| `src/model.py` | Market model: parameters, price equation (6), speed caps (eqs. 9–10), impact cost (8), simulator |
| `src/closed_form.py` | The paper's equilibria: Props. 1, 2, 2′, 7, 8, 9, valuations (Def. 2); the cartel |
| `src/solver.py` | LP best responses (Lemma 1), the cartel LP, fictitious play |
| `src/contagion.py` | Survival hurdles W(I_d) (eq. 21) by sequential LP, equilibria, cascades |
| `src/unequal.py` | Predators with unequal positions (footnote 15) |
| `src/plots.py` | The Fig. 4-style chart shared by the app and figures |
| `app.py` | Streamlit app |
| `figures.py` | Report figures |
| `slides/` | Beamer presentation; uses `figures/` directly |
| `report/` | LaTeX report (11 pages); uses `figures/` directly |
| `tests/` | Every result checked against the paper's numbers or an independent method |
| `PLAN.md` | The 10-week plan |
| `docs/week-NN.md` | What was done each week, how, results, and issues found |

## Results at a glance
- **Replication (weeks 1–4).** Props. 1–9 and Figs. 1–3 reproduced exactly (e.g. price 116 → 100 → 110).
  A batch auction (Prop. 9) lowers the overshoot but does not raise the distressed seller's revenue.
- **Verification (weeks 5–6).**
  - A linear program finds each predator's best possible strategy, and it never beats the paper's.
  - Predators starting from a naive strategy *learn* the predatory equilibrium (fictitious play).
- **Extension F, collusion (week 7).**
  - A cartel keeps the overshoot (13.33) however many members it has.
  - It is a pure transfer from the distressed traders.
  - It is unstable, because members gain by cheating.
  - It preys even where competing predators would have provided liquidity.
- **Extension C, contagion (week 8).**
  - Survival hurdles computed from eq. (21): the best survival strategy sells, then buys at the bottom to prop up its own paper value.
  - Fig. 4's scenarios reproduced, including the ripple D, E → A → B → C, and a bailout that stops it.
- **Stretch A, unequal positions (week 9).**
  - Footnote 15's strategy confirmed as an equilibrium.
  - Its claim that more dispersion means more overshoot is sharpened: only the smallest predator's position matters.
