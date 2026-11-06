# ADR 0002: Make scenario calculations auditable

- Status: accepted
- Date: 2026-11-06

## Context

Proposals and ROI models can appear authoritative even when their inputs are uncertain. The project
requires versioned assumptions and a traceable explanation for every output number.

## Decision

Validate a versioned input profile, calculate base-case money values with `Decimal`, and attach a
stable formula identifier plus exact inputs to every derived metric. Keep exact arithmetic separate
from stochastic estimates and include assumptions and caveats in every export.

## Consequences

- Numeric correctness can be checked against hand-calculated cases.
- Any output can be recomputed from its recorded inputs and formula identifier.
- Rounding happens only at explicit currency-display boundaries.
- Adding a formula requires updating its audit entry and numeric tests.
