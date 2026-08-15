"""Build data/combined_mental_health_dataset.csv from data/raw/*.csv.

Run from the backend directory:

    ./.venv/bin/python data/build_dataset.py

Sources
-------
The existing ``combined_mental_health_dataset.csv`` is preserved verbatim (it is
the curated production corpus and must never shrink). Every CSV in
``data/raw/`` is then added on top, deduplicated against the base and each
other, so this script only ever grows the dataset. Known schemas:

  * ``Questions,Answers``
  * ``Human,Bot``
  * ``Context,Response``
  * ``questionTitle,questionText,answerText`` (counselchat)

Filtering (applied to NEW rows only)
------------------------------------
* drops rows with empty/short questions (< 5 chars) or thin answers (< 40 chars)
* drops rows containing HTML tags or training-template markers (``[INST]``/``<s>``)
* drops exact duplicates and duplicate questions (case-insensitive)
* caps output at ``MAX_ROWS`` to keep the FAISS build fast

Output
------
``data/combined_mental_health_dataset.csv`` with ``Questions,Answers`` header.
"""

from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BACKEND_DIR / "data" / "raw"
OUT_FILE = BACKEND_DIR / "data" / "combined_mental_health_dataset.csv"
MAX_ROWS = 25_000
MIN_QUESTION = 5
MIN_ANSWER = 40
MAX_CHARS = 4000

_TAG_RE = re.compile(r"<\s*(?:s|/s|INST|\[INST\])", re.IGNORECASE)
_HTML_RE = re.compile(r"<[a-z][^>]*>", re.IGNORECASE)


def _clean(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ok_pair(question: str, answer: str) -> bool:
    return (
        len(question) >= MIN_QUESTION
        and len(answer) >= MIN_ANSWER
        and len(answer) <= MAX_CHARS
        and not _HTML_RE.search(answer)
        and not _TAG_RE.search(answer)
    )


def _rows_from_csv(path: Path) -> list[tuple[str, str]]:
    """Extract (question, answer) pairs from a CSV, sniffing the schema."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return []
        headers = {h.strip().lower() for h in reader.fieldnames if h}
        rows = list(reader)

    if {"questions", "answers"} <= headers:
        q, a = "Questions", "Answers"
    elif {"human", "bot"} <= headers:
        q, a = "Human", "Bot"
    elif {"context", "response"} <= headers:
        q, a = "Context", "Response"
    elif {"questiontext", "answertext"} <= headers:
        q, a = "questionText", "answerText"
    else:
        print(f"  [skip] {path.name}: unknown schema {sorted(headers)}")
        return []

    pairs = []
    for row in rows:
        q_text = _clean(row.get(q, ""))
        a_text = _clean(row.get(a, ""))
        if q_text and a_text:
            pairs.append((q_text, a_text))
    return pairs


def main() -> int:
    base: list[tuple[str, str]] = []
    if OUT_FILE.exists():
        print(f"[read] {OUT_FILE.relative_to(BACKEND_DIR)} (existing base)")
        base = _rows_from_csv(OUT_FILE)

    raw_files = sorted(RAW_DIR.glob("*.csv"))
    new_sources: list[tuple[str, list[tuple[str, str]]]] = []
    for path in raw_files:
        pairs = _rows_from_csv(path)
        before = len(pairs)
        pairs = [p for p in pairs if _ok_pair(*p)]
        print(f"[read] {path.relative_to(BACKEND_DIR)}: {before} -> {len(pairs)} after filter")
        new_sources.append((path.name, pairs))

    seen: set[tuple[str, str]] = set()
    seen_q: set[str] = set()
    kept: list[tuple[str, str]] = []
    added = 0

    for name, pairs in [("(existing base)", base)] + new_sources:
        used = 0
        for q, a in pairs:
            key = (q.lower(), a.lower())
            q_key = q.lower()
            if key in seen or q_key in seen_q:
                continue
            seen.add(key)
            seen_q.add(q_key)
            kept.append((q, a))
            used += 1
        if name != "(existing base)":
            added += used
        print(f"  {name}: {len(pairs)} candidate -> {used} new kept")

    if len(kept) > MAX_ROWS:
        print(f"[warn] capping {len(kept)} rows to MAX_ROWS={MAX_ROWS}")
        kept = kept[:MAX_ROWS]

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(["Questions", "Answers"])
        writer.writerows(kept)

    print(f"\n[done] base={len(base)} + new={added} -> total {len(kept)} rows "
          f"-> {OUT_FILE.relative_to(BACKEND_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())