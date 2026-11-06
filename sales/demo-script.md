# Five-minute demo script

> Fictional product demonstration. The sample values are illustrative and are not customer results.

## 0:00–0:45 — Set scope

“This is a fictional QA automation workflow. I will show how the model uses assumptions; it does not
claim a measured automation result.”

## 0:45–1:45 — Review the inputs

Open `examples/fictional-scenario-v1.json`. Identify the release count, regression hours, labor
rate, coverage assumption, license, support, and implementation values. Point out the version,
low/base/high ranges, and notes.

## 1:45–2:45 — Run the base case

Run `solutionfit calculate --input examples/fictional-scenario-v1.json`. Compare modeled costs with
the baseline and read the formula IDs and recorded inputs. Explain that annual savings depend on
every entered assumption.

## 2:45–3:45 — Explore uncertainty

Review the one-at-a-time sensitivity table and the Monte Carlo summary. Show the seed, number of
runs, triangular distributions, and independence caveat. Do not present probability as a forecast.

## 3:45–4:30 — Export the proposal

Open the Markdown and PDF outputs. Confirm the fictional-product label, cost formulas, versioned
input ranges, and caveats are present.

## 4:30–5:00 — Agree on validation

Ask which input needs evidence, who can validate it, and what a bounded next step would be. Do not
present the sample scenario as a quote or offer.
