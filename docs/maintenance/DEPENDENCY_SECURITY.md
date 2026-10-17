# Dependency security updates

Reviewed 2026-10-17 following a supplied pip-audit report of 188 findings across
16 installed packages. The report covers the entire virtualenv, including
packages no longer required by this project; several advisory rows are repeated.

## Persistent requirements

`pyproject.toml` now includes the following security minimums. Transitive packages
are listed explicitly where necessary so ordinary installs, CI, and Docker all
apply the minimums without an additional constraints-file argument. These entries
protect dependencies used by the application; they do not add new features.
FawltyDeps exclusions identify these intentional requirements.

| Package | Reported version | Required minimum | Consumer |
| --- | --- | --- | --- |
| cryptography | 46.0.4 | 50.0.0 | Encrypted Django model fields. |
| djangorestframework | 3.16.1 | 3.17.2 | django-handyhelpers and REST filters. |
| idna | 3.11 | 3.15 | Requests hostname handling. |
| Pillow | 12.1.0 | 12.3.0 | Image fields and image ingestion. |
| Pygments | 2.19.2 | 2.20.0 | Developer-tool output (pytest/Bandit). |
| pytest | 9.0.2 | 9.0.3 | Test runner. |
| requests | 2.32.5 | 2.33.0 | API calls and ingestion. |
| setuptools | 82.0.0 | 83.0.0 | Build backend and hurry.filesize's runtime requirement. |
| soupsieve | 2.8.3 | 2.9.0 | BeautifulSoup selectors. |
| sqlparse | 0.5.5 | 0.6.0 | Django, debug toolbar, and handyhelpers. |
| tornado | 6.5.4 | 6.5.9 | Flower monitoring service. |
| urllib3 | 2.6.3 | 2.8.0 | Requests HTTP transport. |

The build-system section also requires patched setuptools for isolated builds.
All minimum versions were verified against their PyPI release metadata and
support the project's declared Python 3.10 minimum. Installs on newer Python
versions may choose newer compatible releases. Django stays on the 5.2 series;
the existing django-filter compatibility pin remains unchanged.

## Stale virtualenv packages

AnyIO, Authlib, Black, and NLTK are absent from a clean installation of the
current project and its development/Docker extras. The old virtualenv retained
them after dependency declarations were removed. Safety pulled in Authlib and
NLTK; the application does not use these packages. NLTK's reported advisories
include entries without a listed fix, so adding it back with an arbitrary
upgrade would not resolve the report reliably.

Refresh the project environment from its declared requirements to remove these
leftovers. `pip install -e '.[dev]'` alone does not remove packages that were
previously installed. Do not add unused packages back solely to specify a patched
version. Independent experimental scripts that need additional libraries should
use a separate virtualenv and audit those requirements separately.

## Verification scope

Validation uses an isolated source snapshot and virtualenv before changing the
developer environment. Unaffected installed dependency versions are held stable
with temporary validation constraints; affected packages resolve to patched
releases. Those temporary constraints are not committed project pins.

The regression suite includes event ingestion, managed images, encrypted
credential storage/round trips, full/HTMX pages, and the shared helper integration.
No production credentials or media are rewritten. Tests do not ingest live events
or send notifications.

The online pip-audit check was explicitly approved. It sends installed package
names and versions to PyPI's vulnerability service, not application source or
event data. No advisory is suppressed. The local SpokaneTech distribution has
no public PyPI release, so pip-audit cannot assess that distribution itself;
its installed third-party dependencies are audited separately.

## Results

- A clean development/Docker-extra install succeeds. The affected packages resolve
  to cryptography 50.0.2, Django REST framework 3.18.3, idna 3.20, Pillow 13.0.0,
  Pygments 2.21.0, pytest 9.1.1, Requests 2.34.2, setuptools 84.0.0, SoupSieve
  3.0.3, sqlparse 0.6.0, Tornado 6.5.10, and urllib3 2.8.0.
- Online pip-audit: **no known vulnerabilities** across 110 third-party packages.
  Only the local SpokaneTech distribution is skipped. Each proposed minimum
  version was also checked against PyPI's release vulnerability metadata, with
  no listed advisories.
- The developer virtualenv was synchronized to the validated package set.
  A local comparison confirms that all 110 third-party package names and versions
  exactly match the online-audited environment. A second online audit of that
  environment was not performed. AnyIO, Authlib, Black, NLTK, and Safety are absent.
- Full regression suite: **223 tests and 66 subtests passed**. The sole warning
  is an existing invalid string escape in handyhelpers' template tags.
- Django checks, dependency consistency, Mypy (80 files), FawltyDeps, Bandit,
  Ruff lint/format, and diff checks pass. No migration changes are required.

The previous developer package list is saved temporarily at
`/tmp/spokanetech-security-original-venv.txt`. The validated package list and
machine-readable audit report are under `/tmp/spokanetech-security-*` for this
session; these temporary artifacts are not a committed lock file.

Already-running Django/Celery processes need restarting to load updated modules.
Production receives these requirements on its next image build; this work does
not deploy or restart production. Docker image builds, live PostgreSQL/Redis
connections, and real provider scraping were not exercised.
