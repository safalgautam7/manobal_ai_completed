import random

from app import quotes


def test_random_quote_returns_from_file(settings, monkeypatch):
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    q = quotes.random_quote()
    assert isinstance(q, str) and q.strip()


def test_random_quote_empty(monkeypatch):
    monkeypatch.setattr(quotes, "load_quotes", lambda: [])
    assert quotes.random_quote() == ""


def test_load_quotes_skips_blank_lines(settings, tmp_path, monkeypatch):
    f = tmp_path / "q.txt"
    f.write_text("First quote\n\nSecond quote\n", encoding="utf-8")

    object.__setattr__(settings, "quotes_file", str(f))
    quotes.load_quotes.cache_clear()
    loaded = quotes.load_quotes()
    assert loaded == ["First quote", "Second quote"]
    quotes.load_quotes.cache_clear()