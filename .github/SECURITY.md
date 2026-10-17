# Security policy

## Reporting a vulnerability

Email [admin@spokanetech.org](mailto:admin@spokanetech.org) privately with the
subject "SpokaneTech security report". Do not post exploit details, credentials,
or personal information in a public issue or pull request.

Include affected URLs or code, the version or commit if known, reproduction steps,
and the potential impact. Use synthetic data where possible. Do not access other
people's data, disrupt services, or include live secrets to demonstrate an issue.

We will review reports as maintainer availability allows and coordinate disclosure
with the reporter. No response-time guarantee or paid bounty is offered. If you
have not received a reply, follow up using the same private channel.

GitHub's private vulnerability reporting is a separate repository setting. If it
is enabled, the Security tab's "Report a vulnerability" option is also suitable.
The presence of this file does not mean that setting is enabled.

## Maintenance scope

Security maintenance focuses on the current `main` branch and deployed release.
Report concerns affecting older revisions too, but fixes or backports for older
releases are not guaranteed. The declared Python minimum and tested environments
are described in [CONTRIBUTING.md](CONTRIBUTING.md#development-setup).

## Dependency checks

The pip-audit workflow checks installed runtime, development, and Docker-extra
dependencies on pull requests. A clean audit is a point-in-time check of known
third-party advisories, not a guarantee that application code has no security
issues. See [dependency security decisions](../docs/maintenance/DEPENDENCY_SECURITY.md).
