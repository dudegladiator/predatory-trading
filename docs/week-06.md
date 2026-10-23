# Week 6: Learning the equilibrium (iterated best response)

## What was built
| File | Contents |
|---|---|
| `src/solver.py` | `naive_start` (predators just buy steadily, no predation); `deviation_gain` (how much any predator could still gain by deviating); `fictitious_play` (damped best-response dynamics, symmetric or asymmetric) |
| `tests/test_solver.py` | Paper's equilibria have zero deviation gain; symmetric fictitious play converges to Prop. 2; asymmetric play ends symmetric |
| `app.py` | Page 6, "Equilibrium check" |
| `tests/test_app.py` | Page 6 renders, shows 1214.0000 for both the paper's and the best strategy, and scrubs to round 300 without errors |
| `figures.py` | Adds `figures/fictitious_play.png` |

Total: 71 tests passing after the review below (about 12 s; most of it is the fictitious-play tests).

## Step 1: plain best-response iteration cycles (as `PLAN.md` warned)
Each predator in turn switched fully to its best response, from a naive start. Twelve rounds, Fig. 3 example (paper overshoot 3.33 for I = 3, 0.83 for I = 9):

| | Overshoot over rounds 1–12 |
|---|---|
| I = 3 | jumps between 12.2 and 22.0, never settles |
| I = 9 | jumps between 16.8 and 25.6, never settles |

The reason is that best responses are all-or-nothing. Against strategies that leave money on the table, a predator dumps its position, or even shorts, at the full speed cap. Everyone overreacts to everyone else. (Experiment only, not committed.)

## Step 2: fictitious play converges
Each round every predator moves a step of 1/(k + 2) toward its best response, i.e. it plays the average of all its past best responses (classic fictitious play).

- **Symmetric version:** all predators share one strategy; one LP per round. This matches the paper, whose Prop. 2 is the unique *symmetric* equilibrium.
- **Asymmetric version:** each predator keeps its own strategy and responds to the others; all update simultaneously.

**Symmetric, from the naive start** (deviation gains include the impact cost G; see the review below):

| Round | I = 3: max price gap to eq. 20 | I = 3: deviation gain | I = 9: max price gap | I = 9: deviation gain |
|---|---|---|---|---|
| 1 | 13.33 | 22.22 | 13.33 | 65.81 |
| 10 | 7.27 | 5.93 | 14.51 | 19.95 |
| 50 | 1.89 | 0.91 | 4.36 | 3.25 |
| 200 | 0.61 | 0.33 | 1.66 | 0.94 |
| 1000 | 0.24 | 0.13 | 0.53 | 0.30 |

1000 rounds take about 9 s. Convergence is slow but steady, roughly like 1/k, which is typical of fictitious play.

**Step sizes compared** (300 rounds; smaller is better):

| Step | I = 3 price gap / gain | I = 9 price gap / gain |
|---|---|---|
| 1/(k+2) | 0.56 / 0.27 | 1.33 / 0.69 |
| 2/(k+3) | 0.48 / 0.35 | 1.24 / 0.69 |
| 1/√(k+2) | 1.59 / 1.11 | 2.00 / 2.36 |
| constant 0.05 | 1.58 / 0.84 | 4.52 / 2.09 |

1/(k+2) is as good as anything tried, so the code uses the textbook choice.

**Asymmetric, from different starts** (I = 3: one predator buys steadily, the other waits and buys late). Their positions at t0 + τ go 3.58 / 3.08 → 3.343 / 3.289 (round 50) → 3.335 / 3.323 (round 300); the paper's are 3.333 each. Both head to the paper's symmetric equilibrium. That is evidence the dynamics have no asymmetric resting point, which fits the paper's uniqueness claim. It is slower than the symmetric version (gains 1.5 / 2.1 after 300 rounds).

## What the figure shows (`figures/fictitious_play.png`)
- **Round 0:** no predation; the price slides smoothly from 116 to 113.33.
- **Round 10:** predators have learned to prey but overdo it: the price falls to about 105, far below the paper's 110.
- **Round 50 → 300:** the path tightens onto eq. 20. The deviation gain falls from 22 to 0.27 (log scale, Panel B).

Story for the class: **predation is not assumed, it is learned.** Traders who only respond to each other's past behaviour discover the paper's predatory equilibrium on their own.

## Tests
- Deviation gain of the paper's equilibria is below 1e-6 (Prop. 1, Fig. 3 I = 3 and 9).
- Symmetric play, I = 3, 300 rounds: the gain at rounds 0, 10, 50, 100, 300 falls strictly, from above 20 to below 0.3. The price path ends within 0.6 of eq. 20.
- Asymmetric play, I = 3, 100 rounds from different starts: both predators within 0.05 of the paper's position at t0 + τ.

## App page 6
- **Part 1:** pick an example. The page solves the LP live (about 30 ms) and shows the paper's payoff, the best possible payoff (equal) and both holdings paths.
- **Part 2:** a "Round" slider scrubs through fictitious play (rounds 0 … 300), showing the price against eq. 20 and the deviation gain over rounds. Results are cached, so the 2–4 s computation runs once per example.
- This page uses the paper's parameters, not the sidebar sliders, so the computation can be cached and the numbers match the report.

## Limits
- Convergence is slow (fictitious play), so tests use tolerances, not exact equality. A faster scheme is possible, but the textbook one is easier to explain and is enough to show convergence.
- Distressed traders keep the paper's strategy throughout (see week 5).

## Review (start of week 7): averaged strategies can break the speed limit
**Problem.** Fictitious play averages strategies. The speed caps (eqs. 9–10) depend nonlinearly on the other traders' rates, so blended strategies can break them. Measured, as the largest excess over a trader's cap / over A in total:

| Run | Round 1 | Round 10 | Round 100 | Round 300 |
|---|---|---|---|---|
| Symmetric, I = 3 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Symmetric, I = 9 | 6.67 / 40 | 1.01 / 6.06 | 0.11 / 0.66 | 0.04 / 0.22 |
| Asymmetric, I = 3 | 0 / 0 | 0.29 / 0.29 | 0.07 / 0.07 | — |

In the symmetric I = 9 run, each predator's best response is only feasible for one predator if the others stay put. All six adopt it at once, so in round 1 the market trades at 60 against A = 20. The simulator did not model the impact cost G, because the equilibria never pay it. So these off-equilibrium payoffs, and the I = 9 deviation gains above, were too generous.

**Fix.** `simulate` now charges eq. (8)'s cost G, γ = λ·I·x̄ per excess share (the smallest γ the paper allows). Payoffs are therefore honest for any strategy, including mid-learning ones.
- The cap functions moved from `solver.py` to `model.py`, since they are part of the market model, and `solver.py` imports them.
- The caps are only computed at steps where the market as a whole trades faster than A. If |Σ a| ≤ A, no trader can exceed its cap: a_i > ā_i would give a_i + Σ_j a_j ≥ a_i + Σ_j min(a_j, a_i) > A. So the equilibria, which never exceed A, cost no extra time.

**Effect.** The LP best responses never exceed the caps, so the dynamics themselves are unchanged. Only the evaluation of off-equilibrium payoffs changed. The I = 9 deviation gains are now larger early on (65.81 instead of 8.65 at round 1) and still converge (0.30 at round 1000). The I = 3 results and the figure are unchanged. The tables above show the corrected numbers.

**New tests** (`tests/test_impact_cost.py`, 6 tests):
- a hand-computed charge: selling 10 over the cap for 0.1 at γ = 20 costs 20
- the paper's equilibria (Props. 1, 2, 8) pay exactly zero
- the shortcut "total within A ⇒ nobody over their cap" holds on 2,000 random cases
- round 1 of the I = 9 dynamics trades at 60 and is charged

The first version charged about 1e-11 per step to a trader sitting exactly at its cap (rounding), so excesses below 1e-9 are now ignored, as elsewhere in the code.
