# ADR 0003: Use seeded independent triangular simulation

- Status: accepted
- Date: 2026-11-06

## Context

The scenario needs uncertainty ranges, sensitivity analysis, and Monte Carlo results, but no
customer data exists to estimate real distributions or dependencies.

## Decision

Require visible low/base/high values for uncertain inputs. Use independent triangular distributions
with a recorded seed and bounded run count. Keep the exact base case and the simulation summary
distinct in reports.

## Consequences

- Simulation is reproducible and makes its distributional assumptions inspectable.
- Results do not imply probabilities learned from real sales or customer data.
- Correlation is not modeled until defensible data is supplied.
- The CLI records seed, sample count, and percentiles alongside the estimates.
