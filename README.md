# SpokaneTech.org
Home of SpokaneTech.org, an online hub for Spokane's tech events and groups. It's not just a website; it's a community-driven, open-source initiative aimed at fostering learning and collaboration among aspiring and seasoned tech enthusiasts.

<br/>

## Code Quality
| Workflow | Description             | Status                                                                       |
|----------|-------------------------|------------------------------------------------------------------------------|
|Bandit|security checks|![Bandit](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/bandit.yaml/badge.svg)|
|Black|code formatting|![Black](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/black.yaml/badge.svg)|
|Isort|python import ordering|![Isort](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/isort.yaml/badge.svg)|
|Mypy|static type checking|![Mypy](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/mypy.yaml/badge.svg)|
|Radon|code complexity analysis|![Radon](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/radon.yaml/badge.svg)|
|Ruff|static code analysis|![Ruff](https://github.com/SpokaneTech/SpokaneTechWeb/actions/workflows/ruff.yaml/badge.svg)|


<br/>

## Local Development

### prerequisites
1. git installed on system
2. python installed on system (3.10+ recommended)


### local git setup
1. clone the repo:

    ```
    git git@github.com:SpokaneTech/SpokaneTechWeb.git
    ```

2. git config (optional)
To enable pre-commit code quality checks, update the location of git hooks with the following command:

    ```shell
    git config core.hooksPath .github/hooks
    ```

    Note: to make a commit with the precommit hooks temporarily disabled, run the following:

    ```
    git commit --no-verify
    ```

<br/>


### local environment setup steps

1. cd into the repo directory
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
    venv\Scripts\activate
    ```

4. install the python dependencies
    ```
    pip install .[dev]
    ```

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
    ./manage.py runscript init_data
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

open a browser and navigate to http://127.0.0.1:8000 (log in with admin/admin)

** you can stop the local demo server anytime via ```ctrl + c ```
