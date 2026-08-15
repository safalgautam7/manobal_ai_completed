from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import emotion
from app.security import get_current_user

router = APIRouter(tags=["emotion"])


class EmotionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/analyze-emotion")
async def analyze_emotion(
    request: EmotionRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        dominant, score = emotion.analyze_emotion(request.text.strip())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Emotion analysis failed") from exc

    emotion.save_emotion(user_id, dominant, score)
    return {
        "emotion": dominant,
        "score": score,
        "suggestion": emotion.get_emotion_suggestions(dominant),
    }


@router.get("/emotion-graph")
async def emotion_graph(user_id: str = Depends(get_current_user)):
    """Aggregated emotion counts for the current user (no per-request PNG)."""
    return emotion.get_emotion_counts(user_id)