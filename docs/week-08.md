# Week 8: Extension C, contagion, survival hurdles and bailouts

## What was built
| File | Contents |
|---|---|
| `src/contagion.py` | `others_when`, `wealth_change`, `survival_drop` (best survival strategy by sequential LP), `hurdles` (W(I_d) for all I_d), `equilibria`, `cascade` |
| `src/plots.py` | Fig. 4-style chart (wealth bars against hurdle lines), shared by the app and `figures.py` |
| `tests/test_contagion.py` | 11 tests (below) |
| `app.py`, `tests/test_app.py` | Page 8, "Contagion", and its test |
| `figures.py` | Adds `figures/contagion.png` |

Total: 101 tests passing.

## Step 1: a precise definition of the survival hurdle (eq. 21)
The paper defines W(I_d) as the highest wealth at t0 at which trader i *cannot* avoid distress if I_d traders are expected to fail, i included. It gives no formula. Our numerical version:

- **Setting.** The other traders are I_d − 1 distressed traders selling at A/I, plus I − I_d predators preying as in the I_d-distressed equilibrium (Props. 1, 2, 2′), with trader i in a distressed slot. If I_d = I, nobody is left to prey and the others all liquidate.
- **Wealth.** Wealth is mark-to-market: W_i(t) = x_i·p + cash + other assets. Other assets are fixed after the shock at t0. On the grid the change over a step is exactly λ·[(x_{k+1}² − x_k²)/2 + x̄_k·ΔX₋ᵢ,k]. A test checks this against the simulator's x·p + cash path.
- **Hurdle.** W(I_d) = W̲ + D(I_d), where D(I_d) = −max over trader i's strategies of min over t of ΔW_i(t), the smallest worst-case drop it can achieve. D(0) = 0.

## Step 2: solving it
The x² term makes the max–min non-convex, so it is not a plain LP. **Sequential linear programming:**
1. Replace x²/2 by its tangent at the current path. The tangent is never above the curve, so each LP answer is truly achievable.
2. Solve, re-linearize at the new path, and repeat. Each step can only improve.
3. Run it from several starting paths (hold; sell as fast as allowed; sell and go short; buy as fast as allowed) and keep the best.

The LP is sparse: running wealth is a variable linked step to step, so 800 steps solve in well under a second.

**Is it reliable?** In experiments, 25 random starting paths per I_d plus the fixed ones all reached the same values. One random start at I_d = 6 stopped at a worse local optimum (75.0 against 72.0), which is why the code uses several starts. A brute-force search over a family of simple strategies never beat it.

## Finding: the best way to survive is to buy at the bottom
The optimal survival strategy sells at the speed limit for a while, then buys hard up to x̄ just as the price bottoms. The trader's own buying props up the price, and with it the paper value of its holdings, exactly when its wealth would otherwise be lowest. That is allowed by eq. (21), which maximises over all strategies. It matches a real-world effect the paper cites: Attari, Mello & Ruckes (2002) study a distressed trader buying to push up the price.

It also matters a lot. With I_d = 4, the worst-case drop is 63 for the best strategy, against 95 for just holding and 71 for selling out. So, as decided at the start of week 8, the default follows eq. (21) literally, and `can_buy=False` gives the sell-or-hold-only version for comparison.

## Results (six traders A–F: S = 40, μ = 140, λ = 1, A = 20, x̄ = 6, x0 = 5, t0 = 5, T = 9, dt = 0.005)
| I_d | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| D(I_d), any strategy (default) | 0 | 27 | 48 | 63 | 72 | 72 |
| D(I_d), sell or hold only | 5 | 34.5 | 57 | 70.5 | 75 | 75 |

- **Prop. 4 holds:** the hurdle rises with the number of expected failures, strictly up to I_d = 5, under both rules.
- **Flat from 5 to 6.** With one predator left, it sells alongside the distressed traders just as a sixth distressed trader would, so the trough trader i must survive is the same.
- **D(1) = 0 by default.** With only one share of predator selling, the trader can buy enough to keep its mark-to-market wealth from ever falling.

## Step 3: contagion (Fig. 4)
With W̲ = 100 the hurdles are W(1..6) = 100, 127, 148, 163, 172, 172. Following Fig. 4:
- A sits in (W(1), W(2)], B in (W(2), W(3)], C in (W(3), W(4)].
- D, E, F are safe: wealth 115, 140, 155, 200, 200, 200.

**Rules.**
- An outcome with I_d failures is consistent (an equilibrium) if exactly I_d traders have wealth ≤ W(I_d).
- The **ripple** starts from the traders forced out (wealth ≤ W̲) and keeps adding traders who fall below the hurdle for the current number of failures. It ends at the smallest equilibrium at or above the forced failures.

| Scenario | Consistent outcomes | Ripple | Paper |
|---|---|---|---|
| No shock (Panel A) | 0 failures only | nobody fails | "no strategic trader is in distress" ✓ |
| D shocked to 90 (Panel B) | 1, 2, 3 or 4 failures | D only | "equilibria in which 1, 2, or 3 [or 4] traders face distress" ✓ |
| D and E shocked | 5 only (unique) | D, E → A → B → C | "the ripple-effect equilibrium is unique" ✓ |
| D and E shocked, D bailed out | 1–4 | E only | "a bailout of one or two traders … can stabilize prices" ✓ |

Panel B's multiple outcomes are the paper's panic story: if the market expects four failures, predation is fierce enough to cause them.

## App page 8
- Pick a scenario, adjust each trader's wealth, choose who the central bank bails out, and toggle the hurdle rule.
- Shows the Fig. 4-style chart, the ripple step by step, all consistent outcomes, the hurdle table, and the price path with the resulting number of failures.
- Hurdles are cached per rule (about 1 s each to compute). Fuzzed with 40 random settings: 0 crashes.

## Tests (`tests/test_contagion.py`)
- The wealth formula equals the simulator's mark-to-market path (to 1e-8).
- Hurdle values pinned for both rules.
- Prop. 4: hurdles non-decreasing, and strictly increasing up to I_d = 5.
- The best survival strategy does at least as well as holding, and its reported drop matches its path.
- All four scenarios in the table above, including the exact ripple order.

## Limits
- The cascade uses wealth at t0 and the paper's one-shot logic: who is below the hurdle for the expected number of failures. Traders' wealth is not re-simulated along the cascade.
- Sequential LP finds a local optimum. Multi-starts and the random-start experiment make a missed better strategy unlikely, but it is not a proof.
- Bailouts are modelled as recapitalisation (wealth raised above every hurdle). Other forms, such as a central bank buying the distressed position, are not modelled.

## Review (start of week 9)
Checked against the plan's "done when" criteria: Fig. 4 scenario reproduced, bailout stops the cascade, W(I_d) rises with I_d. All met.

- **Time-step check.** Hurdles use dt = 0.005 (the rest of the project uses 0.001) to keep the LPs small. Recomputed at dt = 0.005, 0.0025 and 0.001 under both rules, the values are identical (0, 0, 27, 48, 63, 72, 72 and 0, 5, 34.5, 57, 70.5, 75, 75). They are exact, not grid artifacts, because every switch time falls on the grid. The coarse step only saves time: 2 s against 30 s.
- **Consistency.** `hurdles` now builds parameters with `dataclasses.replace`, like the rest of the code.
