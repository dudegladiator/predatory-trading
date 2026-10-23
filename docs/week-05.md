# Week 5: LP best response, an independent check of the equilibria

## What was built
| File | Contents |
|---|---|
| `src/solver.py` | `speed_caps` (eqs. 9–10, the equal-priority speed limits); `best_response` (one trader's optimal strategy against fixed opponents, as a linear program) |
| `tests/test_solver.py` | Speed-cap cases; the paper's strategies checked as best responses for Props. 1, 2, 2′, 8; the LP beating a non-equilibrium strategy; constraints respected |

Total: 60 tests passing (after the review below).

## How it works
**Why it is a linear program.** Lemma 1: with x_i(0) and x_i(T) fixed, trader i's payoff (11) on our grid is a constant minus

  λ · Σ_k a_k · dt · (X₋ᵢ,k + X₋ᵢ,k+1) / 2

where X₋ᵢ is everyone else's holdings. Trader i's own price impact cancels out, which is the paper's point that predation is not manipulation. Once the opponents are fixed, X₋ᵢ is fixed, so the payoff is linear in trader i's trades. The LP optimum is therefore the exact best response in the discretized game, not an approximation of it.

**Formulation.** The variables are trader i's holdings x_0 … x_N, not its rates. That keeps the position limit |x| ≤ x̄ as simple variable bounds, and the speed limits become a sparse two-band matrix on x_{k+1} − x_k. x_0 = x(t0) and x_N = target (x̄ for a predator, per Lemma 1) are fixed by their bounds. Solved with SciPy's HiGHS in 10–30 ms for 2,000 steps.

**Speed caps (eqs. 9–10).** Given the others' rates, trader i's fastest buying rate ā solves ā + Σ_j min(a_j, ā) = A. If exactly k of the others are below ā, the left side is (m − k + 1)·ā plus the sum of those k rates, so the code tries every k and keeps the consistent one. This is exact, with no iteration. The selling cap is the mirror image.

Examples (A = 20):
- The distressed trader alone selling at 10 lets the predator sell at most 10 more, but buy up to 30.
- Another trader buying at 15 still leaves trader i a buying share of 10, not 5. That is equal priority: orders share the limit A, rather than the first trader taking it.

## Finding: a sign typo in the paper's eq. (10)
The published paper prints eq. (10) as `a̲ + Σ max{a_j, a̲} = A`, confirmed on the rendered page, not just in the text extraction. Taken literally, a trader facing an inactive market could never sell. That contradicts eq. (7), which caps |Σ a| in both directions, and Prop. 1, where the predator sells at A/I. The right side must be −A, which is what the code uses. Worth a footnote in the report.

## Results: the paper's strategies are best responses
For the last predator in each case, holding everyone else at the paper's strategy:

| Case | Paper's strategy pays | LP best response pays |
|---|---|---|
| Prop. 1 (paper example) | 1214.000000 | 1214.000000 |
| Prop. 2, I = 3 | 787.111111 | 787.111111 |
| Prop. 2, I = 9 | 261.444444 | 261.444444 |
| Prop. 2′, I = 3, x0 = 4 | 702.000000 | 702.000000 |
| Prop. 8, I = 3, t1 = 5.5 | 791.111111 | 791.111111 |

The tests check this for every predator, not just the last, with tolerance 1e-6.

The LP's strategy can differ from the paper's and still pay the same, because footnote 13 says the buy-back speed is free. So the tests also check the part that is pinned down:
- Prop. 1: a best response has sold everything by the time the distressed trader is out (t = 5.8).
- Prop. 2: a best response holds exactly the paper's position at t0 + τ.

**Is the check sensitive?**
- A predator that just buys from t0 gains more than 1 by switching to the LP's strategy, and the LP lands exactly on the equilibrium payoff.
- With the speed caps removed (a one-off experiment, not committed), the LP earns 1324.38 instead of 1214, so a wrong cap would fail the tests.

## Limits
- Best responses are computed for predators only. A distressed trader's rule, "sell at least A/I while holding shares" (eq. 3), depends on its own position, so it is not a fixed linear constraint. Distressed traders keep the paper's strategy throughout.
- x_i(T) = x̄ is imposed, following Lemma 1, rather than chosen by the LP (choosing it would add a quadratic term). The review below checks that it is optimal.
- The batch auction (Prop. 9) is not covered: the LP models continuous trading only.

Next, week 6: iterate best responses from naive starting strategies and see whether they converge to Prop. 2.

## Review (start of week 6)
Lemma 1's x_i(T) = x̄ was only assumed, so it is now tested. For each end position from −x̄ to x̄ (9 values), the LP finds the best payoff, and that payoff rises strictly all the way to x̄. Checked in three cases:
- Prop. 1: 414 → … → 1214
- Prop. 2, I = 3: 342.67 → … → 787.11
- Prop. 2′: 102 → … → 702

No other issues found.

Note (week 7 review): `speed_caps` has since moved to `src/model.py`, where the simulator also uses it to charge the impact cost G. See `docs/week-06.md`.
