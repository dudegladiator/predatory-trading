# Week 3: Valuation, disclosure, front-running, batch auction (Props. 5–9)

## What was built
| File | Contents |
|---|---|
| `src/model.py` | `simulate(..., auction=)`: optional block trades at t0 in a batch auction; `Paths.start_price` (price before any auction) |
| `src/closed_form.py` | `prop7_x0`; Prop. 8 `prop8_tau`, `prop8_rates`, `prop8_price` (eqs. 24–25); Prop. 9 `prop9_trades`, `prop9_price` (eq. 26) |
| `tests/test_valuation.py` | Props. 5–6 |
| `tests/test_disclosure.py` | Prop. 7 |
| `tests/test_market_design.py` | Props. 8–9 |
| `figures.py` | Adds `prop56_valuation.png`, `prop7_disclosure.png`, `prop89_market_design.png` |

Test count: 40, all passing (after the review fix below).

## How each piece works
- **Distressed liquidation value (Def. 2 iii)**: a distressed trader's cash at T in the equilibrium simulation, i.e. what it actually raised while being preyed on.
- **Batch auction (Section VI.B)**: block trades happen at t0 at one clearing price, the price after all block trades on the demand curve. `start_price` keeps the pre-auction price, so overshoot is measured against where the market was before the auction.
- **Front-running (Prop. 8)**: distressed traders start selling only at t1. Predators sell from t0 at A/I_p, using the whole speed limit, until each one's X₋ᵢ reaches (I_p − 1)·x̄. They wait until t1, then buy while the distressed traders sell. The code asserts front-running ends before t1, and that predators do not short past −x̄ (see review below).
- **Prop. 7** is the paper's closed form only. The investment phase (choosing x(t0) before t0) is not simulated; the week 5–6 solver could check it.

## Results
**Props. 5–6, valuation.** Paper > orderly > distressed value holds for the Prop. 1 example (928 > 896 > 864) and the Fig. 3 examples with I = 3, 9. With more predators the total distressed value rises (I = 3 … 30), but stays below the orderly value even at 200 predators (≈ 683 vs 690).
Prop. 6's condition, `x0 ≥ x̄·√(I_p/I)`, fails for the Fig. 3 example (16 < 16.33), so these tests use I·x0 = 18 instead of 16.

**Prop. 7, disclosure.** Disclosure always shrinks the initial position, e.g. I=5, π=0.5: 8.75 vs 9.0. Either way the position stays above the predation threshold (I_p − 1)/(I − 1)·x̄, so predation still happens. That is the paper's claim, checked for I ∈ {3, 5, 10}, π ∈ {0.1, 0.5, 0.9}.

**Props. 8–9, market design** (Fig. 3 example, I = 3, front-running with t1 = 5.5):

| Market | Lowest price | Overshoot | Distressed revenue |
|---|---|---|---|
| Front-running | 108.00 | 5.33 | 590.2 |
| Normal (Prop. 2) | 110.00 | 3.33 | 598.2 |
| Batch auction | 112.00 (auction) | 1.33 | 597.3 |

Simulated prices equal eqs. (25) and (26) at every grid point. A single predator stays out of the auction, as Section VI.B says.

## Finding: a smaller overshoot does not mean a better price for the seller
I first assumed the batch auction also raises the distressed trader's revenue. It does not; the paper only claims a smaller overshoot. Across seven setups:

| Setup | Overshoot normal → batch | Revenue normal → batch |
|---|---|---|
| I=2 (one predator), x0=8 | 10.0 → 2.0 | 864.0 → 864.0 |
| I=2, x0=9.5 | 10.0 → 0.5 | 1040.25 → 1040.25 |
| I=3, x0=5.33 | 3.33 → 1.33 | 598.22 → 597.33 |
| I=3, x0=6 | 3.33 → 0.67 | 676.22 → 676.00 |
| I=9 (Fig. 3) | 0.83 → 0.44 | 201.26 → 200.69 |
| I=27 (Fig. 3) | 0.26 → 0.15 | 67.23 → 67.07 |
| I=3, two distressed | 10.0 → 4.0 | 654.0 → 636.0 |

With continuous trading, the distressed trader sells its first shares at prices near 116. In the auction everything goes at one price. With one predator the two effects cancel exactly; with more predators the auction is slightly worse for the seller. The auction does stabilise the price path, which is what the paper argues. Worth a paragraph in the report.

## Review fix: Prop. 8 can break the position limit
During front-running each predator sells down to `x0 − A·τ/I_p`. Prop. 8 does not say this must stay above −x̄, and it does not always: with I = 5, three distressed traders, x0 = 9, x̄ = 10, eq. (24) would take each predator to −17. `prop8_rates` now refuses such inputs, and a test checks that every simulated path keeps |x| ≤ x̄. The paper's own examples are unaffected (I = 3 bottoms at 1.33). Another hidden condition for the report, alongside Prop. 2′'s.
