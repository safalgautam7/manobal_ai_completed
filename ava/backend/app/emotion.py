"""Emotion analysis backed by a Hugging Face text-classification pipeline.

The pipeline (torch) is heavy, so it is loaded lazily on first use and cached.
Results are persisted to SQLite so the graph endpoint can aggregate counts
without scanning a growing JSON file, and so each user only sees their own data.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Tuple

from app import db


@lru_cache(maxsize=1)
def get_analyzer():
    from transformers import pipeline

    from app import config

    settings = config.get_settings()
    return pipeline(
        "text-classification",
        model=settings.emotion_model,
        device=settings.emotion_device,
        return_all_scores=True,
    )


def analyze_emotion(text: str) -> Tuple[str, float]:
    """Return ``(dominant_emotion, confidence)`` for the given text."""
    analyzer = get_analyzer()
    results = analyzer(text)
    # transformers 4.x returns [[{label,score}, ...]] while 5.x returns
    # [{label,score}, ...] for a single input — normalize both shapes.
    scores_list = results[0] if results and isinstance(results[0], list) else results
    scores = {res["label"]: res["score"] for res in scores_list}
    dominant = max(scores, key=scores.get)
    return dominant, scores[dominant]


def save_emotion(user_id: str, emotion: str, score: float) -> None:
    db.save_emotion(user_id, emotion, score)


def get_emotion_counts(user_id: str | None = None) -> dict[str, int]:
    return db.get_emotion_counts(user_id)


def get_emotion_suggestions(emotion: str) -> str:
    suggestions = {
        "joy": "It's great to hear that you're feeling happy! Keep spreading that positivity.",
        "sadness": "It's okay to feel sad sometimes. Reaching out to a friend or journaling can help.",
        "fear": "It's normal to feel anxious. Deep breathing or talking to someone can help you relax.",
        "anger": "Try taking a break or talking to someone about what's bothering you.",
        "disgust": "If you need to vent, I'm here to listen. Talking things out can help.",
        "surprise": "Surprises can be exciting and overwhelming. Would you like to share more?",
    }
    return suggestions.get(emotion, "I'm here to listen. Feel free to talk about what's on your mind!")