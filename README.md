# SolutionFit Sales Engineering

SolutionFit is a local proposal and scenario-modeling toolkit for **QualityPath**, a fictional QA
automation product. The example inputs are explicitly illustrative; there are no customer names,
quotes, market benchmarks, or realized savings in this repository.

The project demonstrates ICT sales-engineering work through a transparent cost comparison,
discovery guide, five-minute demo plan, objection-handling guide, one-page solution brief, and
proposal exports. Every model output can be traced to a versioned assumption and formula. Scenario
results are estimates, not promises.

## Run locally

Python 3.12 is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\solutionfit.exe calculate --input examples\fictional-scenario-v1.json
```

The command writes `output\proposal.json`, `output\proposal.md`, and `output\proposal.pdf`.
The default simulation uses 10,000 runs and seed 42. For a reproducible alternate run:

```powershell
solutionfit calculate --input examples\fictional-scenario-v1.json --runs 10000 --seed 42
```

All calculation output includes the assumption version, base/range inputs, formula IDs, audit
inputs, sensitivity results, simulation seed, distribution, and caveats.

## Check and build

```powershell
python -m pytest --cov=solutionfit --cov-report=term-missing
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src tests
```

Build and run in a local container:

```powershell
docker compose run --rm solutionfit
```

## Project structure

- `src/solutionfit/`: validated assumptions, exact financial formulas, sensitivity, Monte Carlo,
  JSON/Markdown/PDF rendering, and CLI.
- `examples/fictional-scenario-v1.json`: fully labeled, versioned illustrative inputs.
- `sales/`: discovery, demo, objection, and one-page solution materials.
- `docs/adr/`: accepted product, math, simulation, and export decisions.
- `BENCHMARKS.md`: real 10,000-run simulation benchmark and methodology.
- `RESUME_BULLETS.md`: verifiable project outcomes only.

## Limitations

The product and scenario are fictional. Automation coverage is a user-entered assumption, not a
validated product result. Workload and costs are held constant over the selected horizon.
Monte Carlo uses independent triangular input distributions because no data supports correlation.
No financial, accounting, legal, procurement, or investment advice is provided.
