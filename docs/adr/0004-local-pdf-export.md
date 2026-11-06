# ADR 0004: Generate proposal PDFs locally

- Status: accepted
- Date: 2026-11-06

## Context

The project must export a proposal as PDF without sending potentially sensitive assumptions or
business context to a hosted conversion service.

## Decision

Render the PDF in-process with ReportLab from the validated proposal model. Use plain text styles,
wrap long content, and include fictional-product and assumption caveats in the document.

## Consequences

- Export works offline and produces a reproducible local artifact.
- The PDF implementation is a presentation layer and cannot recalculate financial values.
- PDF text and metadata require tests to ensure the caveats and audit summary are included.
