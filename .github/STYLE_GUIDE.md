# SpokaneTech style guide

Use clear names, focused functions, and comments that explain decisions. Follow
PEP 8 with the project's configured formatting choices. The configuration in
[pyproject.toml](../pyproject.toml) is authoritative for automated checks.

## Formatting and checks

Ruff formats the project with a target line length of 120 characters. This is a
formatting target, not a guarantee that every string or URL will fit. Do not
manually fight the formatter. Run these commands from the repository root:

```shell
ruff format src
ruff check src
mypy src
```

Use `ruff format src --check` for validation without edits. Black and Isort are
not separate project formatting requirements. Ruff's configured lint checks and
mypy's current configuration do not enforce every convention below; these are
review expectations for new and changed code, not a demand for unrelated rewrites.
See [CONTRIBUTING.md](CONTRIBUTING.md#validation) for the complete check list.

## Naming

Use `CapWords` for classes, `snake_case` for functions and variables, and
`UPPER_SNAKE_CASE` for constants. Prefer names that describe a value or operation.
Do not shadow built-ins such as `list` or `dict`. Boolean names such as `is_valid`
can be useful, but container-type suffixes such as `_list` are not required.

```python
MAX_RETRIES = 3


class Calculator:
    """Provide simple arithmetic operations."""

    def add(self, left: float, right: float) -> float:
        return left + right
```

## Type annotations

Keep examples and changes compatible with the declared Python 3.10 minimum.
Use `:` for parameter and variable annotations and `->` for return annotations;
they are complementary syntax, not alternative styles.

Annotate new or substantially changed function interfaces where useful. Prefer
inference for obvious local values and annotate empty collections or ambiguous
values when type checking requires it. A descriptive name does not replace a
function's type contract. Avoid `Any` or `type: ignore` merely to silence an
uninvestigated error; explain necessary exceptions.

```python
from collections.abc import Callable

Coordinates = tuple[float, float]


def calculate_total(items: list[float]) -> float:
    return sum(items)


def describe_location(location: str | None) -> str:
    return location or "Location to be announced"


def apply_function(function: Callable[[int, int], int], left: int, right: int) -> int:
    return function(left, right)
```

Prefer built-in collection annotations (`list[str]`, `dict[str, int]`) and
`X | None`/`X | Y` unions in new code. Use `-> None` for functions that return no
value. Existing compatible annotations do not require unrelated cleanup.
Do not use Python 3.12's `type` alias statement while Python 3.10 is supported.

## Docstrings and comments

Use concise docstrings for modules, classes, and functions when they add useful
context. Explain behavior, side effects, and non-obvious constraints. For longer
interfaces, use Google-style `Args`, `Returns`, and `Raises` sections as needed.
Avoid restating an obvious name or type merely to fill a template.

```python
def calculate_sum(numbers: list[float]) -> float:
    """Add the supplied numbers.

    Args:
        numbers: Values to add.

    Returns:
        The total, or zero when the list is empty.
    """
    return sum(numbers)
```

## Examples and documentation

Use standard GitHub Markdown code fences with a language name. Code examples
should parse and include required imports. Use `pass` or `...` when showing an
intentional placeholder body; a comment alone is not a valid function body.
Keep claims about supported versions and enforced checks aligned with the actual
configuration. Link to [the README](../README.md#local-development) for virtualenv
setup rather than duplicating platform-specific installation instructions.
