"""Normalize current and legacy group icons for escaped template attributes."""

import re

from bs4 import BeautifulSoup


def get_icon_classes(value: str) -> str:
    """Extract Font Awesome classes without rendering stored HTML or its attributes."""
    classes: list[str]
    if "<" in value:
        icon = BeautifulSoup(value, "html.parser").find("i")
        attribute = icon.get("class") if icon else None
        if isinstance(attribute, str):
            classes = attribute.split()
        else:
            classes = list(attribute) if attribute is not None else []
    else:
        classes = value.split()
    return " ".join(name for name in classes if re.fullmatch(r"fa(?:[brsld]|-[a-z0-9-]+)?", name))
