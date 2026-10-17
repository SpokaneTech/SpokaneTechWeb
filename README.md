# SpokaneTech.org
Home of SpokaneTech.org, an online hub for Spokane's tech events and groups. It's not just a website; it's a community-driven, open-source initiative aimed at fostering learning and collaboration among aspiring and seasoned tech enthusiasts.


See the live site here:
https://www.spokanetech.org

Follow development here:
https://spokanetech.github.io/blog/building-spokane-tech/intro/
<br/>

## Code Quality
| Workflow | Description             | Status                                                                       |
|----------|-------------------------|------------------------------------------------------------------------------|
|Bandit|security checks|![Bandit](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/bandit.yaml/badge.svg)|
|FawltyDeps|dependency checks|![FawltyDeps](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/fawltydeps.yaml/badge.svg)|
|Mypy|static type checking|![Mypy](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/mypy.yaml/badge.svg)|
|pip-audit|dependency vulnerability checks|![pip-audit](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/pip_audit.yaml/badge.svg)|
|PyTest|unittest execution|![Pytest](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/pytest.yaml/badge.svg)|
|Radon|code complexity analysis|![Radon](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/radon.yaml/badge.svg)|
|Ruff Format|code formatting|![Format](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/ruff_format.yaml/badge.svg)|
|Ruff Lint|static code analysis|![Lint](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/ruff_lint.yaml/badge.svg)|


<br/>

## Search discovery and organic growth

Public pages include per-page search/social metadata, a sitemap, and guides
backed by current groups and events. Development and staging default to noindex.
Production must explicitly set `SEO_INDEXING_ENABLED=True` and configure
`PUBLIC_SITE_URL` when deploying these changes. Event structured data requires
individual eligibility review; notification promotion links are a separate opt-in.

See the [rollout guide](docs/growth/SEO_IMPLEMENTATION_AND_ROLLOUT.md),
[organic outreach playbook](docs/growth/ORGANIC_OUTREACH_PLAYBOOK.md), and
[search account setup](docs/growth/SEARCH_ENGINE_OWNERSHIP_SETUP.md).

## Local Development

### prerequisites
1. git installed on system
2. Python 3.10+ installed on system (required for Django 5.2)


### Fork and clone

Forking is the recommended contribution path. Use GitHub's
[Fork button](https://github.com/SpokaneTech/SpokaneTechWeb/fork), then clone your
fork rather than the upstream repository. Replace `YOUR_USERNAME` below:

```shell
git clone https://github.com/YOUR_USERNAME/SpokaneTechWeb.git
cd SpokaneTechWeb
git remote add upstream https://github.com/SpokaneTech/SpokaneTechWeb.git
git switch -c describe-your-change
```

Push your branch to your fork and open a pull request targeting
`SpokaneTech/SpokaneTechWeb:main`. See the
[contribution guide](.github/CONTRIBUTING.md) for updating your fork, validation,
reporting issues, and review expectations.

To enable optional local pre-commit checks:

```shell
git config core.hooksPath .github/hooks
```

The hook checks formatting without editing files. Run `ruff format src` yourself
to apply formatting before committing.

### local environment setup steps

1. from the directory containing your clone, cd into the repo directory (skip if already there)
    ```
    cd SpokaneTechWeb
    ```

2. create a python virtual environment
    ```
    python -m venv venv
    ```

3. activate the python virtual environment
    
    for linux, mac, or wsl:
    ```
    source venv/bin/activate
    ```
    for powershell:

    ```powershell
    .\venv\Scripts\Activate.ps1
    ```

4. install the python dependencies
    ```
    python -m pip install -e '.[dev]'
    ```
    The editable install also adds `spokanetech-manage` to the active virtual
    environment. It accepts the same arguments as `manage.py` and can be run
    from the repository root or another directory:

    ```shell
    spokanetech-manage check
    spokanetech-manage migrate
    spokanetech-manage runserver
    ```

    After adding or changing the shortcut, rerun the install command above.

5. (optional) create a custom .env file and update contents as applicable
    ```
    cp src/envs/.env.template src/envs/.env.local
    ```

6. cd to the django_project directory
    ```
    cd src/django_project
    ```

7. create a local database by running django migrations
    ```
    ./manage.py migrate
    ```

8. create a local admin user
    ```
    ./manage.py add_superuser --group admin
    ```

9. (optional) add platforms and groups to your local database
    ```
    ./manage.py runscript initialize_data
    ```

10. (optional) ingest future events to your local database
    ```
    ./manage.py runscript ingest_events
    ```
    Note: this requires playwright and its dependencies to be installed on your system. 
    ```playwright install --with-deps```

11. start the local demo server
    ```
    ./manage.py runserver
    ```

Open http://127.0.0.1:8000 and sign in with the credentials you configured for your local administrator account.

** you can stop the local demo server anytime via ```ctrl + c ```

### Frontend static assets

Third-party browser packages load from pinned CDN URLs with integrity checks in
`src/django_project/core/templates/base.htm`. The application does not require
static files from handyhelpers' `node_modules` directory. Site styles, scripts,
and images remain in Django static assets.

Bootstrap is loaded once from CDN. The committed `spokanetech.css` contains the
site's theme overrides only. After changing its Sass source, regenerate it from
the repository root:

```shell
sass --style expanded src/django_project/core/static/spokanetech/css/spokanetech.scss src/django_project/core/static/spokanetech/css/spokanetech.css
```

Sass is an optional editing tool; deployments serve the committed CSS directly.
See [the static assets review](docs/ui/redesign/STATIC_ASSETS_REVIEW.md) for the
package inventory, framework recommendation, and validation details.

### Event images and persistent media

Meetup and Eventbrite ingestion saves event images into a shared persistent media
volume. `runscript ingest_events` downloads images synchronously; scheduled
ingestion uses background Celery image tasks. See the [design decision and VPS rollout guide](docs/design/decisions/0001-persistent-event-images.md)
for migrations, reverse-proxy configuration, local development, and backups.

### Project policies

- [Code of Conduct](.github/CODE_OF_CONDUCT.md)
- [Private security reporting](.github/SECURITY.md)
- [Privacy policy](https://www.spokanetech.org/privacy/)
- [Terms of service](https://www.spokanetech.org/terms/)

Python 3.10+ is declared by the project. Current CI runs on Python 3.13, while the
Docker image uses Python 3.12; there is currently no full Python-version test matrix.
