from fastapi import APIRouter, HTTPException

from app import quotes

router = APIRouter(tags=["quotes"])


@router.get("/random-quote")
async def random_quote():
    quote = quotes.random_quote()
    if not quote:
        raise HTTPException(status_code=503, detail="No quotes available")
    return {"quote": quote}