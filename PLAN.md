# Predatory Trading: Implementation Plan

**Paper:** Brunnermeier & Pedersen (2005), "Predatory Trading", *Journal of Finance* 60(4)
**Owner:** Harsh (solo) · **Duration:** 10 weeks · **Deliverables:** Streamlit app first, then a report and slides

## Goal
1. Reproduce the paper's results with a discrete-time simulator.
2. Confirm the paper's equilibria with an independent numerical solver.
3. Extend the model in two ways: **collusion vs competition (F)** and **contagion cascade with bailout (C)**.

## Stack and layout
Python 3.13 managed with **uv**: NumPy, SciPy (`linprog`), Matplotlib, Streamlit, pytest.

```
predatory-trading/
  PLAN.md
  predatory_trading.pdf
  pyproject.toml    # uv project; run with `uv run ...`
  src/
    model.py        # parameters, price equation p = μ − λ(S − X), simulate(rates) → paths
    closed_form.py  # Props 1, 2, 2′, 8, 9 strategies; valuations (Def. 2); Prop 7
    solver.py       # LP best response, iterated best response, collusion optimum
    contagion.py    # wealth, survival hurdle W(I_d), cascade, bailout
  tests/            # paper's numbers as assertions
  figures.py        # reproduces the paper's figures into figures/
  app.py            # Streamlit, one page per result
```

Commands: `uv run pytest`, `uv run python figures.py`, `uv run streamlit run app.py`.

## Acceptance checks (written as tests)
With the paper's parameters: S=40, μ=140, λ=1, A=20, t0=5, T=7.

| Check | Expected |
|---|---|
| Prop 1 (I=2, x̄=10, x(t0)=8) | Price 116 → 100 at t=5.8 → 110 at t=6.3 |
| Prop 1, "one share less" deviation (Fig 2 dotted line) | Marginal share sold at an average of 101.00, bought back at 100.50 |
| Def. 2 valuation, single predator | Paper 928 > orderly 896 > distressed 864 |
| Fig 3, I=3 / 9 / 27 (1/3 distressed, Ix(t0)=16, Ix̄=20) | Lowest price ≈ 110 / 112.5 / 113.08, long-run price 113.33, so overshoot 3.33 / 0.83 / 0.25 |
| Prop 7 | x(t0) = (1−π/I)x̄ without disclosure, (1−π/(I−1))x̄ with it |
| Props 8, 9 | Overshoot ordering: front-running > normal > batch auction |

The Fig 3 and valuation numbers are derived from the paper's formulas; week 2 confirms them against the figures.

## Weekly plan

| Week | Work | Done when |
|---|---|---|
| **1** | uv project setup. `model.py`: time grid, positions, price, cash, wealth. Prop 1 in `closed_form.py`. | Prop 1, deviation and valuation tests pass. Figs 1–2 reproduced. |
| **2** | Props 2, 2′, 3. Sweep the number of predators. | Fig 3 reproduced. Overshoot falls toward 0 as the number of predators rises. |
| **3** | Props 5–6 (valuation vs number of predators), Prop 7 (disclosure), Props 8–9 (front-running, batch auction). | All acceptance tests pass. |
| **4** | Streamlit pages 1–5: model, single predator, many predators, valuation & disclosure, market design. | **Checkpoint 1:** the replication app runs end to end with live sliders. |
| **5** | `solver.py`: LP best response for one trader with others held fixed. Objective (Lemma 1): min Σ aₜ·X₋ᵢ,ₜ·dt. Constraints: speed bounds from the equal-priority rule (eqs. 8–10), \|x\| ≤ x̄, x(T) = x̄. | The LP's best response to the Prop 1 and Prop 2 strategies gives the same payoff as the paper's strategy. |
| **6** | Iterated best response, starting from naive strategies (e.g. everyone buys immediately). Page 6 with a convergence animation. | Converges to Prop 2's price path and payoffs for I = 3 and 9. |
| **7** | **Extension F, collusion.** Predators maximize joint profit, i.e. act like one predator with capacity I_p·x̄. Solved in closed form and confirmed with the joint-objective LP. Page 7. | Chart of competitive vs collusive overshoot and distressed loss vs number of predators. |
| **8** | **Extension C, contagion.** Wealth W_i = x_i·p + O_i. Compute the hurdle W(I_d) numerically following eq. 21, then run the cascade: shock trader D, then A, B, C fail one by one. Add a bailout toggle. Page 8. | Fig 4 scenario reproduced. The bailout stops the cascade. W(I_d) rises with I_d (Prop 4). |
| **9** | Polish the app and catch up on slippage. Stretch, if ahead: A (unequal starting positions), B (crisis λ). | **Checkpoint 2:** feature-complete app. |
| **10** | Report (model, replication, verification, extensions, policy) and slides. | Report and deck finished. |

## Known risks
- **The best response isn't unique.** The paper's footnote 13 says the buyback speed doesn't matter. So iterated best response won't land on exactly the paper's strategies; compare price paths and payoffs instead. If plain iteration oscillates, fall back to damping (average each new response with the previous one, as in fictitious play).
- **The equal-priority speed rule (eqs. 8–10) must be implemented exactly.** A simple "total speed ≤ A" cap changes the game, because one predator could take all the capacity.
- **The hurdle W(I_d) has no closed form.** Week 8 starts by writing down a precise numerical definition based on eq. 21 before any code.
- **Discretization error.** dt sets the accuracy. Choose dt so switch times fall on the grid; tests use a tolerance, and results are checked to converge as dt shrinks.

## Out of scope unless time allows
Extensions A, B, D, E; RL; empirical NSE or crypto data.
