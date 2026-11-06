# Operations lifecycle

## Start

- Install the project in a Python 3.12 virtual environment.
- Review the fictional assumptions in `examples/fictional-scenario-v1.json`.
- Run the documented `solutionfit calculate` command.
- Inspect JSON, Markdown, and PDF exports before sharing.

## Stop

- No service runs persistently; exit the CLI when the calculation completes.
- Keep or remove local files under `output/` according to the scenario's sensitivity.

## Roll back

- Restore the previous versioned assumption file or code revision.
- Re-run calculation and compare all outputs, seed, and formula IDs.
- Do not silently replace a saved scenario with unreviewed assumptions.

## Common failures

- **Profile rejected**: check version, required fields, visible fictional label, and low/base/high
  constraints.
- **Undefined payback**: the modeled annual net savings are not positive under the current inputs.
- **PDF unavailable**: reinstall project dependencies and confirm ReportLab is installed.
- **Unexpected result**: inspect audit input values and formula IDs before changing assumptions.
