# Week 9: Polish, and stretch A (unequal positions, footnote 15)

Scope agreed at the start of the week: polish plus stretch A. Stretch B (crisis λ) is left out, because Lemma 1's structure breaks when λ varies over time and it would need a new solver.

## Polish
| Item | Result |
|---|---|
| Test warnings | The 35 warnings all came from inside Streamlit (a pandas deprecation in its chart code). `pyproject.toml` now ignores exactly that message, so any new warning will show. Test output is clean. |
| `README.md` | How to run tests, figures and the app; a map of `src/`, `tests/`, `docs/`; results at a glance; issues found in the paper |
| Fuzz pass, all 8 pages | 30 random slider settings per page. Found one crash on the new page (below), fixed; then 0 crashes. |

## Stretch A: predators with unequal positions
### What was built
| File | Contents |
|---|---|
| `src/model.py` | `Params.holdings`: optional per-trader holdings at t0 (default: everyone holds x0); `Params.start()`. Used by the simulator. |
| `src/solver.py` | `best_response` reads each trader's own starting holdings. The cartel solver refuses unequal holdings. |
| `src/closed_form.py` | The closed forms now refuse unequal holdings instead of silently using x0. |
| `src/unequal.py` | `switch_time`, `footnote15_rates` (the footnote's strategy, built step by step), `predicted_overshoot` |
| `tests/test_unequal.py` | 11 tests (below) |
| `app.py`, `tests/test_app.py` | Page 9, "Unequal positions", and 2 tests |
| `figures.py` | Adds `figures/unequal_positions.png` |

Total: 115 tests passing, no warnings.

### The footnote's strategy
The paper describes it only in words (footnote 15):
1. Everyone sells at A/I until the X₋ᵢ of the predator with the **smallest** position falls to its final level (I_p − 1)·x̄. Call that time s.
2. Predators then buy at I_d·A / (I·(m − 1)) each, where m is the number still buying. That keeps each buyer's X₋ᵢ flat.
3. As predators reach x̄ and stop, the rest speed up.

The footnote does not cover the last buyer (m = 1 would divide by zero). Our reading: it waits until the distressed traders are out, then buys at the full speed A. The solver confirms that this is right.

### Verified as an equilibrium
For each case the LP best response (week 5) gains nothing over the footnote's strategy (deviation gain below 1e-6):
- I = 3, predators at x0 ± 0.5 and x0 ± 1
- I = 4, predators at x0 − 0.4, x0, x0 + 0.4 and x0 − 0.8, x0, x0 + 0.8 (this exercises the speed-up rule)

With equal positions it reduces exactly to Prop. 2 (I = 3 and 9).

**Grid note.** At first, with dt = 0.001, I = 3 ± 0.5 showed a gain of 0.0067. The switch time s = 5.3375 falls between grid points; at dt = 0.0005, where it falls on one, the gain is exactly 0. `footnote15_rates` now averages the rate over the step containing s, which cuts the off-grid error to about 4e-5. The tests use grids where s falls on a point, so they are exact.

### Finding: only the smallest predator matters
The paper claims, without proof, that "for fixed aggregate holdings of all predators at t0, the price overshooting increases with the dispersion of the initial holdings". Confirmed: for I = 3, the overshoot goes 3.33 → 4.08 → 4.83 for δ = 0, 0.5, 1.

The mechanism gives a sharper statement. The trough is at the switch time s, and s depends on the positions only through the smallest predator's, plus the total. So

  overshoot = λ·[A·(s − t0) − (X0 − I_p·x̄)],  with s − t0 = (X0 − x_min − (I_p − 1)·x̄) · I / ((I − 1)·A).

The overshoot rises by λ·I/(I − 1) for each unit the smallest position sits below the rest, and the rest of the spread is irrelevant. Tested: I = 4 with predators at (3.2, 4.0, 4.8) and at (3.2, 4.4, 4.4) have different spreads but the same smallest position. Both give an overshoot of exactly 41/15 = 2.7333, matching the formula, and both are equilibria. The simulated overshoot matches the formula across the whole range of δ (`figures/unequal_positions.png`, Panel B).

The intuition: the smallest predator has the most of everyone else's selling still ahead of it (the highest X₋ᵢ), so it keeps selling longest, and everyone keeps selling with it.

### Other tests
- The switch time is Prop. 2's t0 + τ = 5.3 for equal positions, and 5.375 for I = 3 ± 1.
- Positions above x̄ are rejected (δ is at most x̄ − x0 = 1.33 for the Fig. 3 totals).

### App page 9
- Uses the same trader sliders as the other pages, plus a spread δ: predators are placed evenly from x0 − δ to x0 + δ.
- Shows the overshoot with equal and with spread positions, the formula's prediction, the price paths, and each predator's holdings.
- **Fuzz-found crash.** With total holding equal to total capacity (x0 = x̄), there is no room to spread, and the δ slider had min = max = 0. The page now shows a note instead. Regression test added; it checks that the note actually appears.

## Limits
- Distressed traders are assumed to hold equal positions; only the predators' positions differ.
- The equilibrium is verified with the LP (no profitable deviation), not derived; uniqueness is not checked.
