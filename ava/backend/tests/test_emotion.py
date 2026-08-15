import pytest

from app import emotion


def test_analyze_emotion_returns_dominant(monkeypatch):
    class FakeAnalyzer:
        def __call__(self, text):
            return [[{"label": "joy", "score": 0.8}, {"label": "sadness", "score": 0.2}]]

    monkeypatch.setattr(emotion, "get_analyzer", lambda: FakeAnalyzer())
    dominant, score = emotion.analyze_emotion("i am so happy today")
    assert dominant == "joy"
    assert score == pytest.approx(0.8)


def test_analyze_emotion_flat_format_transformers5(monkeypatch):
    class FakeAnalyzer:
        def __call__(self, text):
            return [{"label": "fear", "score": 0.9}, {"label": "joy", "score": 0.1}]

    monkeypatch.setattr(emotion, "get_analyzer", lambda: FakeAnalyzer())
    dominant, score = emotion.analyze_emotion("anxious")
    assert dominant == "fear"
    assert score == pytest.approx(0.9)


def test_emotion_saved_and_counted(settings):
    emotion.save_emotion("user-x", "fear", 0.6)
    emotion.save_emotion("user-x", "fear", 0.5)
    emotion.save_emotion("user-y", "joy", 0.9)
    assert emotion.get_emotion_counts("user-x") == {"fear": 2}
    assert emotion.get_emotion_counts("user-y") == {"joy": 1}


def test_suggestions_fallback():
    assert emotion.get_emotion_suggestions("joy").startswith("It's great")
    assert "listen" in emotion.get_emotion_suggestions("neutral")