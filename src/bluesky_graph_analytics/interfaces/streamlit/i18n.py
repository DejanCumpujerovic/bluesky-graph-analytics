"""UI strings from locales/<locale>.json (dotted keys)."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd

LOCALE = "sr"
_LOCALES_DIR = Path(__file__).parent / "locales"


def _flatten(tree: dict[str, Any], prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in tree.items():
        full = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{full}."))
        else:
            flat[full] = str(value)
    return flat


@cache
def strings(locale: str = LOCALE) -> dict[str, str]:
    with (_LOCALES_DIR / f"{locale}.json").open(encoding="utf-8") as fh:
        return _flatten(json.load(fh))


def t(key: str, default: str | None = None, **kwargs: Any) -> str:
    text = strings().get(key, key if default is None else default)
    return text.format(**kwargs) if kwargs else text


def translate_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: t(f"columns.{c}", default=str(c)) for c in df.columns})
