# Dependency review

Reviewed 2026-10-17 against application imports, migrations, Django settings,
management commands, tests, Git hooks, workflows, Docker configuration, and
installed package metadata. This supersedes the dependency candidates in
[the unused-code removal plan](UNUSED_CODE_REMOVAL_PLAN.md).

Follow-up: [the dependency security update](DEPENDENCY_SECURITY.md) adds explicit
security minimums for affected direct and transitive packages and refreshes the
developer environment. The verification results below describe the earlier
unused-dependency review, before those security upgrades.

## Removed declarations

| Package | Reason |
| --- | --- |
| `django-braces` | No application, configuration, migration, or installed handyhelpers consumer. |
| `packaging` | No application imports; supplied transitively by Kombu and developer tools. |
| `redis` | Supplied by `celery[redis]`, including the broker transport's version constraints. Redis support remains enabled. |
| `coveralls` | No coverage-upload integration. The [pinned reusable pytest action](https://github.com/davidslusser/actions_python_pytest/blob/v1.0.1/action.yaml) only installs dependencies and runs pytest. |
| `faker` | No application or test imports; tests generate model data with model-bakery. |
| `isort` | No current workflow or hook invocation; Ruff handles formatting. It remains a transitive requirement of FawltyDeps. |
| `mypy-extensions`, `typing_extensions` | No project imports; mypy supplies these dependencies. |
| `safety` | No workflow or hook invocation. The existing `pip-audit` dependency is retained for dependency security checks. |
| `types-python-dateutil` | No project imports of dateutil. Library-internal uses do not require the project to install its type stubs. |

Black was already removed from the developer dependencies before this review.
Removed its leftover configuration, the unused Isort configuration, and obsolete
FawltyDeps exclusions. Added a FawltyDeps exclusion for the `pip-audit` command.
Removing a redundant declaration does not uninstall a package that another
dependency requires.

## Retained runtime dependencies

| Packages | Consumer |
| --- | --- |
| `django` | Application framework, ORM, templates, admin, and management commands. |
| `django-handyhelpers` | Models, views, URL routes, context processor, templates, and commands. |
| `django-filter==25.1` | Compatibility constraint for handyhelpers' REST filtering dependency; retain the validated version. |
| `django-environ` | Settings and environment configuration. |
| `django-fernet-encrypted-fields` | Model fields and historical migrations storing encrypted credentials. |
| `django-celery-beat` | Installed Django app and database-backed task scheduler. |
| `celery[redis]` | Background tasks, worker/beat commands, and Redis broker/backend support. |
| `flower` | Monitoring service in Docker Compose. |
| `django-extensions` | Installed app; documented `runscript` ingestion and initialization commands. |
| `django-debug-toolbar` | Enabled automatically for local/dev deployments, including base-only installs. |
| `beautifulsoup4`, `requests`, `playwright` | Event ingestion, HTML processing, API calls, and browser-based scraping. |
| `Pillow` | Django image fields and event image validation/processing. |
| `psycopg2-binary` | PostgreSQL backend used in production. |
| `whitenoise` | Configured static-file middleware and storage. |
| `gunicorn` (Docker extra) | Production web server used by the container entrypoint. |

## Retained developer dependencies

| Packages | Consumer |
| --- | --- |
| `bandit`, `mypy`, `ruff` | Current CI workflows and local pre-commit checks. |
| `fawltydeps` | Dependency consistency workflow. |
| `radon` | Complexity analysis workflow. |
| `pytest`, `pytest-django`, `model-bakery` | Test execution, Django integration, and model fixtures. |
| `pytest-cov` | Local coverage reports using the repository's coverage configuration. |
| `types-requests` | Type checking of the application's requests calls. |
| `pip-audit` | Existing developer dependency for manual dependency vulnerability checks. |

From the repository root, after installing `.[dev]`, contributors can run:

```shell
pytest --cov --cov-report=term-missing
fawltydeps
pip-audit
```

## Verification

Validation uses fresh Python 3.13 environments containing only the reduced
project dependencies and their transitive requirements. Existing installed
versions are used as temporary validation constraints where compatible; these
constraints are not new project pins. Redis is resolved through the Celery extra:
the tested Celery/Kombu versions select redis-py 6.4.0, rather than the incompatible
7.1.0 present in the original development environment. This is the Python client
version, independent of the Redis server image in Compose.

Results:

- Fresh development plus Docker-extra installation: 111 distributions; dependency
  consistency checks pass. Confirmed `django-braces`, Faker, Coveralls, Safety,
  and the dateutil stubs are absent. Required transitive packages remain installed.
- Fresh Docker-extra installation without development packages: 62 distributions;
  dependency consistency and Django system checks pass. Management command
  discovery, ingestion task registration, Redis transport, PostgreSQL driver,
  Playwright, Gunicorn, and Flower imports pass.
- Full test suite in the fresh development environment: 223 tests and 66 subtests
  pass with coverage enabled (75% across the selected application modules).
- Mypy passes for 80 source files; FawltyDeps, Bandit, Ruff lint/format, and
  `git diff --check` pass. The retained `pip-audit` CLI loads successfully; a live
  vulnerability audit was not part of this unused-dependency review.

The original developer virtualenv is not modified. Validation does not ingest
live events, send notifications, or change application databases. Live PostgreSQL,
Redis connections, browser scraping, and a Docker image build are outside this
dependency review's checks.
