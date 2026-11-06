# Security

## Reporting

Report suspected vulnerabilities privately to the repository owner. Do not include secrets,
personal information, employer/client material, or customer assumptions in public issues.

## Scope and OWASP applicability

SolutionFit reads local JSON, calculates bounded numeric scenarios, and writes local reports. It
does not make network requests, execute user expressions, or accept credentials.

- **A01 Broken Access Control**: no accounts or protected resources exist.
- **A02 Cryptographic Failures**: no secrets or sensitive network traffic are handled.
- **A03 Injection**: inputs are parsed as JSON and numbers; formulas are fixed code, not user text.
- **A04 Insecure Design**: explicit fictional labeling, visible assumptions, bounds, and audit
  formulas reduce misleading proposal risk.
- **A05 Security Misconfiguration**: the container runs non-root with read-only filesystem and no
  network requirement.
- **A06 Vulnerable and Outdated Components**: CI runs pip audit and generates a CycloneDX SBOM.
- **A07 Identification and Authentication Failures**: no authentication is implemented.
- **A08 Software and Data Integrity Failures**: tests verify formulas; input versions and random
  seed are retained in exports.
- **A09 Security Logging and Monitoring Failures**: the CLI reports explicit errors locally and
  sends no telemetry.
- **A10 Server-Side Request Forgery**: not applicable; the application performs no network access.

Proposal assumptions can still be commercially sensitive if a user adds real information. Keep
private scenarios out of source control and review exports before sharing them.
