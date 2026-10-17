# Contributing to SpokaneTech.org

Contributions to code, design, documentation, and testing are welcome. Please
follow our [Code of Conduct](CODE_OF_CONDUCT.md) and [style guide](STYLE_GUIDE.md).

## Reporting issues

Search [existing issues](https://github.com/SpokaneTech/SpokaneTechWeb/issues)
before opening a bug report, feature request, or question. Include reproduction
steps and relevant environment details. Remove credentials, webhook URLs,
tokens, and personal information from screenshots and logs.

Report suspected vulnerabilities privately using [SECURITY.md](SECURITY.md),
rather than a public issue. For conduct concerns, contact
[admin@spokanetech.org](mailto:admin@spokanetech.org).

## Development setup

Follow the [README setup instructions](../README.md#local-development) for Python,
the virtualenv, environment configuration, database setup, and optional ingestion.
Python 3.10+ is declared in `pyproject.toml`; Django stays on the 5.2 series.
Current CI checks use Python 3.13; the Docker image uses Python 3.12. This is not
a claim that CI tests every supported Python version. Changes should preserve
Python 3.10 syntax compatibility unless the minimum is deliberately changed.

## Contributing through a fork

Forking is the recommended path; you do not need write access to this repository.

1. [Fork SpokaneTechWeb](https://github.com/SpokaneTech/SpokaneTechWeb/fork) into
   your own GitHub account.
2. Clone your fork, replacing `YOUR_USERNAME` below with your GitHub username:

   ```shell
   git clone https://github.com/YOUR_USERNAME/SpokaneTechWeb.git
   cd SpokaneTechWeb
   git remote add upstream https://github.com/SpokaneTech/SpokaneTechWeb.git
   git switch -c describe-your-change
   python -m venv venv
   ```

3. Activate the virtualenv as described in the README, then install editable
   project dependencies:

   ```shell
   python -m pip install -e '.[dev]'
   ```

4. Make focused changes, update relevant documentation, and run applicable checks.
5. Commit your changes and push the branch to your fork:

   ```shell
   git push -u origin describe-your-change
   ```

6. Open a pull request from your fork's branch to
   `SpokaneTech/SpokaneTechWeb`'s `main` branch. Explain the problem, resulting
   behavior, related issues, and how you verified it. Maintainers review the PR;
   opening one does not require pushing to the upstream repository.

Before starting a later contribution, update your local main branch from upstream:

```shell
git fetch upstream
git switch main
git merge --ff-only upstream/main
git switch -c another-change
```

If your local main has diverged, resolve that deliberately rather than forcing
an update that discards work.

## Validation

Run commands from the repository root with the virtualenv active:

```shell
ENV_PATH="$PWD/src/envs/.env.test" DEBUG=False pytest
bandit src -c pyproject.toml -r
mypy src
ruff check src
ruff format src --check
fawltydeps
pip-audit
```

The environment prefix shown for pytest uses POSIX shell syntax. In PowerShell,
set `$env:ENV_PATH` to the absolute path of `src/envs/.env.test` and
`$env:DEBUG = "False"` before running pytest. Use the test environment rather
than local or production credentials. Tests use an isolated test database.

Run focused tests while developing and the full suite before requesting review
when application behavior changes. Some tests intentionally log simulated
exceptions; a passing test can exercise an error path. Add meaningful regression
coverage when behavior changes. Explain when tests are not applicable.

Use `ruff format src` separately to apply formatting. The optional
[pre-commit hook](hooks/pre-commit), enabled through the README instructions,
checks formatting without modifying files. CI checks run on pull requests,
including those from forks, without requiring production secrets. Relevant
checks should pass before a maintainer merges; branch-protection enforcement
is configured separately in GitHub settings.

## Documentation and policies

Keep setup instructions in the README and link to them rather than maintaining
another setup walkthrough. Public privacy and terms pages are linked from the
website footer. When changing policy wording, update both the corresponding
`.github` Markdown policy and its `web/partials/custom` template; regression tests
check that the published text matches the repository copy. Update their effective
dates together. Do not invent retention periods, consent mechanisms, or services
that are not configured.

## License

Contributions to the repository's software are made under its existing
[GNU GPL version 3 license](../LICENSE). This does not change the rights of
third-party event descriptions, images, trademarks, or linked services.
