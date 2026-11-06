# ADR 0001: Use an explicitly fictional product

- Status: accepted
- Date: 2026-11-06

## Context

The project specification prefers the user's TestLens project but permits a clearly fictional
product if it is unavailable. No TestLens code or product source was found in the workspace.

## Decision

Use the name QualityPath for a fictional QA automation product. Label it fictional in the README,
sample assumptions, proposal exports, and sales enablement content. Treat all scenario inputs as
visible illustrative assumptions; do not create customer names or claim realized outcomes.

## Consequences

- The project remains runnable without private or user-supplied product material.
- Product capabilities and financial inputs must remain conspicuously hypothetical.
- Replacing QualityPath with TestLens later requires explicit product evidence and reviewed
  assumptions, not a silent relabeling.
