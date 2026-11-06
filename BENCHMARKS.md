# SolutionFit simulation benchmark

## 10,000-run scenario Monte Carlo

The script loads the versioned illustrative scenario, measures one unprofiled simulation, then runs
a separate profiled simulation with the same seed. It verifies both outputs match. All runs are
synthetic and local; no customer or network data is used.

Environment: Windows 11 Pro build 26300, AMD Ryzen 7 5825U with Radeon Graphics, 28.9 GiB RAM,
Python 3.12.10. Runs measured on 2026-11-06 with seed 42.

Commands:

```powershell
python scripts/bench_simulation.py --runs 10000 --seed 42 --profile simulation-before.prof
python scripts/bench_simulation.py --runs 10000 --seed 42 --profile simulation-after.prof
```

| Version | Elapsed | Throughput | Profile result matched |
|---|---:|---:|---|
| Before optimization | 0.473202 s | 21,132.63 runs/s | Yes |
| After optimization | 0.328202 s | 30,469.03 runs/s | Yes |

Throughput increased by 44.2% and elapsed time fell by 30.6% in this run. The profile identified
construction of 12 full audit entries per Monte Carlo sample as avoidable work: the simulation
needs only annual net savings and year-one ROI for each sample. The optimized path shares the same
validated formula core and creates the full audit trail for the exact base case, while using a
small result object for simulation samples.

The optimized result is checked against the former full-audit calculation path for seeded percentile
and probability outputs. This is a local microbenchmark, not a claim about a sales workflow or
customer data.
