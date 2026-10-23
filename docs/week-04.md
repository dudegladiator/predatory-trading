# Week 4: Streamlit app, pages 1–5 (Checkpoint 1)

Run: `uv run streamlit run app.py`

## What was built
| File | Contents |
|---|---|
| `app.py` | Five pages built on the tested `src/` functions; no model logic of its own |
| `tests/test_app.py` | Renders every page headlessly with Streamlit's `AppTest` |
| `pyproject.toml` | pytest path now also includes the project root, so tests can import `app` |

## Pages
| Page | Inputs | Shows |
|---|---|---|
| The model | — | Story, price equation, Lemma 1 intuition, page guide |
| Single predator (Prop. 1) | x̄, x(t0), number of distressed traders | Holdings and price charts; price at t0, lowest, long-run, overshoot; paper / orderly / distressed value |
| Many predators (Props. 2, 2′, 3) | I, I_d, total holding I·x(t0), total capacity I·x̄ | Which regime applies (predation or Prop. 2′); holdings and price; overshoot as the same totals are split among 1×…20× as many traders |
| Valuation & disclosure (Props. 5–7) | Same trader sliders; I and π for disclosure | Distressed value vs number of predators against the orderly and paper values; x(t0) vs π with and without disclosure, plus the predation threshold |
| Market design (Props. 8–9) | Trader sliders; t1 (when front-run traders start selling) | Price paths for normal, front-running and batch auction; overshoot and distressed revenue table |

The sidebar sets λ, A and T for every page. S = 40, μ = 140, t0 = 5 are fixed.
Defaults are the paper's examples, so each page opens on a known result (e.g. 116 → 100 → 110).

## Design decisions
- **Inputs outside the paper's assumptions** (too little time, I·x̄ ≥ S, Prop. 2′'s or Prop. 8's hidden conditions) show a yellow warning naming the broken condition, not a crash. They come from the assertions added in weeks 2–3, caught in one helper, `attempt()`.
- **Native Streamlit charts** (`st.line_chart`) instead of matplotlib: hover tooltips and zoom for the live demo. `figures.py` keeps producing the static report figures.
- **Navigation under `if __name__ == "__main__"`.** Streamlit runs the file as `__main__`, so the app works as normal. Tests can import `app` and render each page function on its own. `AppTest.switch_page` only works with file-based pages, so it couldn't be used.
- **Prop. 3 sweep** keeps the totals fixed and multiplies the number of traders (and distressed traders) by k = 1…20, matching the paper's comparison. The sweep stops at the first k that breaks an assumption.

## Verification
- `tests/test_app.py` (11 tests):
  - every page renders at its defaults with no exception and no warning
  - the single-predator page shows 116.00 / 100.00 / 110.00 and a distressed value of 864.0
  - the many-predators page shows a lowest price of 110.00 and overshoot 3.33 (Fig. 3, I = 3)
  - a bad input (I·x̄ = 76 > S) produces a warning, not an exception
  - I = 2 regression test (below)
- **Fuzzing (not committed):** 240 runs with random values on every slider of pages 2–5. The first run found one crash: with I = 2 the I_d slider had min = max = 1, which Streamlit rejects. Fixed by showing "Distressed I_d: 1" instead of a slider. After the fix: 0 crashes.
- The real entry point (`AppTest.from_file("app.py")`) runs with no exceptions.
- Total: 49 tests passing. The 19 warnings come from inside Streamlit (a pandas deprecation), not from our code.

## Not yet checked
The app has not been viewed in a browser: layout, chart readability and slider feel need a human look.

## Review (start of week 5)
- The market-design caption said the batch auction "removes" the overshoot's cause; an overshoot of 1.33 remains, so it now says the auction *reduces* the overshoot.
- Removed a no-op line (setting T to its default) from `test_bad_inputs_warn_instead_of_crashing`.
