"""Random mental-health quote selection with in-memory caching."""

from __future__ import annotations

import random
from functools import lru_cache

from app import config


@lru_cache(maxsize=1)
def load_quotes() -> list[str]:
    path = config.get_settings().quotes_file
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def random_quote() -> str:
    quotes = load_quotes()
    if not quotes:
        return ""
    return random.choice(quotes)