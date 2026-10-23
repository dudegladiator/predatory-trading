# Week 7: Extension F, collusion vs competition

## What was built
| File | Contents |
|---|---|
| `src/closed_form.py` | `collusion_rates`: the cartel's strategy |
| `src/solver.py` | `collusive_response`: the cartel's joint-profit LP. The shared LP code was factored out into `_optimal_holdings`; `best_response` uses it too, with unchanged behaviour (all earlier tests pass) |
| `tests/test_collusion.py` | 11 tests (below) |
| `app.py`, `tests/test_app.py` | Page 7, "Collusion", and its test |
| `figures.py` | Adds `figures/collusion.png` |

Total: 88 tests passing after the review below.

## The idea
The paper mentions collusion only in words (Section III.A): colluding predators "jointly act like a single predator", selling until the distressed traders are out and only then rebuilding. It also notes that tacit collusion cannot occur in the model. We build the cartel two independent ways, check that they agree, and measure what the paper does not: how big the effect is, and how tempting it is to cheat.

## How it works
**Closed form.** Each predator sells at A/I alongside the distressed traders until they are out at t0 + x0·I/A. Then all rebuild together at A/I_p each (the whole speed limit), which takes I_p·x̄/A. With one predator this is exactly Prop. 1; a test checks that.

**Joint LP.** The Lemma 1 algebra also works for the group. Let P be the predators' total holdings. Their total payoff is a constant minus λ ∫ (dP/dt) · (distressed holdings) dt. So the cartel is one LP for a single trader with capacity I_p·x̄, facing only the distressed traders. For the speed limit, applying eq. (9) to the group as one trader gives the same cap as the sum of its members' caps when they trade equally. Checked by hand: selling, −I_p·A/I; buying, A + I_d·A/I. The group's trades are then split equally.

## Results (Fig. 3 totals: I_d/I = 1/3, I·x0 = 16, I·x̄ = 20)
| I | Overshoot, competing → cartel | Distressed revenue, competing → cartel | Predators' total payoff, competing → cartel | Gain from cheating on the cartel |
|---|---|---|---|---|
| 3 | 3.33 → 13.33 | 598.22 → 576.00 | 1574.22 → 1596.44 | 16.67 (2.1% of a member's 798.22) |
| 9 | 0.83 → 13.33 | 603.78 → 576.00 | 1568.67 → 1596.44 | 11.34 (4.3% of 266.07) |
| 27 | 0.26 → 13.33 | 605.06 → 576.00 | 1567.38 → 1596.44 | — |

- **The cartel's overshoot does not shrink with size.** It always sells down to 100 = μ − λS, so the overshoot is λ·I_p·x̄ = 13.33 however many members it has. With competing predators the overshoot falls toward 0 (Prop. 3).
- **A pure transfer.** The predators gain exactly what the distressed traders lose (22.22 at I = 3, 27.78 at I = 9; tested to 1e-6). Long-term investors are unaffected, matching the paper's remark that predation does not exploit them.
- **Collusion is not stable.** A cartel member gains by cheating: buying back early, before the others. This confirms numerically that collusion is not an equilibrium of this game, as the paper argues. The gain from cheating is a larger share of a member's profit in a larger cartel (2.1% → 4.3%), the usual reason big cartels are harder to hold together.

## Tests (`tests/test_collusion.py`)
- The closed-form cartel equals the joint-LP optimum (total predator payoff to 1e-6) for I = 3 and 9, and never pays the impact cost.
- A one-predator cartel is exactly Prop. 1.
- For I = 3, 9, 27: the cartel's lowest price is 100, its overshoot 13.33 and above the competing one; distressed revenue falls and the predators' total payoff rises.
- The gain from cheating is above 1 for I = 3 and 9.
- Collusion is a pure transfer for I = 3, 9, 27.

## App page 7
- Uses the same trader sliders as the other pages, and shows overshoot, distressed revenue, the predators' joint payoff (each against competition) and the gain from cheating, from one live LP.
- A price chart compares competing and cartel predators.
- An overshoot sweep shows competition eroding the overshoot while the cartel keeps it.
- Fuzzed with 80 random slider settings: 0 crashes.

## Figure (`figures/collusion.png`)
- Panel A: price paths for I = 3 (trough 110 competing, 100 cartel).
- Panel B: overshoot vs number of predators.
- Panel C: the distressed traders' total revenue vs number of predators.

## Limits
- The cartel is assumed to split trades equally. Another split with the same total (and within each member's caps) gives the same *total* payoff, but divides it differently among members.
- Repeated play, where a cartel could punish cheaters and so make tacit collusion possible, is outside this model. The paper says so too (footnote 16), and it is the subject of the Carlin, Lobo & Viswanathan (2007) follow-up.

## Review (start of week 8)
Two cases the tests did not cover. Both checked, then added as tests (4 new, 15 in `tests/test_collusion.py`):

- **The joint LP's output, split equally, stays within every member's speed cap.** Impact cost exactly 0 for I = 3, 9 and the spare-capacity case.
- **Spare capacity (Prop. 2′ regime), I = 3, x0 = 4, x̄ = 10.** Competing predators do not prey here: they buy at once and the overshoot is 0. The cartel still preys: it sells everything first, the price goes 112 → 100 → 120, and the overshoot is 12. The closed-form cartel equals the joint-LP optimum here too (1448.00), and also at x0 = 2 and for I = 4 with two distressed traders.

**Finding for the report:** collusion matters most where competition would have protected the distressed trader. With plenty of sidelined capital, competing predators provide liquidity (Prop. 2′), but a cartel turns that same capital back into predation.
