import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import chat, db
from app.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompt", tags=["chat"])


class PromptRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)


@router.post("")
async def process_prompt(
    request: PromptRequest,
    user_id: str = Depends(get_current_user),
):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    session_id = db.get_or_create_session(request.session_id, user_id)
    try:
        answer = await chat.generate_response(query, session_id, user_id)
    except Exception as exc:  # noqa: BLE001 - surface a friendly message downstream
        logger.exception("Failed to generate response for user %s", user_id)
        raise HTTPException(status_code=502, detail="Could not generate a response right now") from exc

    if not answer:
        answer = "I can help you with mental health-related questions. What would you like to know?"

    return {"response": answer, "status": "success", "session_id": session_id}