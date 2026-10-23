# Week 2: Multiple predators (Props. 2, 2′, 3) and Fig. 3

## What was built
| File | Contents |
|---|---|
| `src/closed_form.py` | Prop. 2 strategies (eq. 19), `prop2_tau`, price path (eq. 20); Prop. 2′ strategies; `preys()` to pick between them; `equilibrium_rates()` picks Prop. 1, 2 or 2′; `_check_assumptions()` |
| `src/model.py` | `schedule()` (step-averaged rates); `Paths.overshoot()` |
| `tests/test_prop2.py` | Checks against the paper's Fig. 3 example, Prop. 2′, Prop. 3, the speed limit |
| `tests/test_prop1.py` | Added: several distressed traders with one predator; assumption checks |
| `figures.py` | Adds `fig3_multiple_predators.png` and `prop3_overshoot.png` |

## The equilibria implemented
Distressed traders always sell at A/I until they are out at `t0 + x0·I/A`.

- **Prop. 2 (predation)**, when `x0 ≥ (I_p − 1)/(I − 1) · x̄`: each predator sells at A/I for `τ = (x0 − (I_p − 1)/(I − 1) · x̄) / (A/I)`, then buys at `A·I_d / (I·(I_p − 1))` until the distressed traders are out. That buying speed keeps each predator's X₋ᵢ (everyone else's holdings) flat, which is what makes no predator want to deviate.
- **Prop. 2′ (no predation)**, when x0 is below that threshold: each predator buys at `A(I + I_d)/(I_p·I)` (the market's whole speed limit, shared equally) until X₋ᵢ reaches its final level `(I_p − 1)·x̄`, then at `A·I_d / (I·(I_p − 1))`. The paper's text extraction garbled this proposition's τ, so it was re-derived from those two conditions: `τ = ((I_p − 1)x̄ − (I − 1)x0) / (A · (1 − (I + I_d)/(I_p·I)))`. That matches what is readable in the paper.

## Results (Fig. 3 setup: a third of traders distressed, I·x0 = 16, I·x̄ = 20)
| I | Lowest price | Long-run price | Overshoot |
|---|---|---|---|
| 3 | 110.00 | 113.33 | 3.33 |
| 9 | 112.50 | 113.33 | 0.83 |
| 27 | 113.08 | 113.33 | 0.26 |

- The simulated price equals eq. (20) at every grid point for I = 3, 9, 27.
- Predators hold exactly x̄ when the distressed traders are out.
- Prop. 3: overshoot is positive, strictly falls for I = 3 … 147, and is below 0.001 at 20,000 predators.
- Prop. 2′ (I=3, x0=4, x̄=10): the price never falls and the overshoot is 0.
- Total trading speed never exceeds A in any equilibrium.

## Decisions and fixes
- **Step-averaged rates (`schedule`).** At first, rates were sampled at step midpoints. For I = 27, τ falls between grid points, so predators ended at 0.74092 instead of x̄ = 0.74074. `schedule()` now gives each step the strategy's average rate over that step. Holdings and prices are exact at every grid point wherever switches fall; cash is off by O(dt²) per switch that falls inside a step.
- **Overshoot definition.** "Final price − lowest price" wrongly reported Prop. 2′'s steady rise (112 → 120) as an overshoot of 8. It is now how far the price drops below both its starting and long-run levels.
- **Assumption checks.** Every strategy asserts the paper's limited capital (I·x̄ < S) and that trading finishes by T. The paper's own time condition, `t0 + 2x̄I/A < T`, is sufficient but stricter than needed. Its Fig. 3 example only meets it with equality, so the check uses each strategy's actual finish time.
- **Fig. 3, Panel A** plots each predator's holdings × I/3 so the three cases share an axis, matching the paper's axis range.

## Note for the report
Prop. 2′ silently assumes the fast-buying phase ends before the distressed traders are out. With I=3, I_d=1, x̄=10 this fails for x0 < 3.33, and the paper does not cover that case. The code raises an error there rather than return a wrong path.
