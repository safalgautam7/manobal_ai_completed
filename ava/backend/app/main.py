"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, db
from app.routers import chat as chat_router
from app.routers import emotion as emotion_router
from app.routers import health as health_router
from app.routers import quotes as quotes_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


def create_app() -> FastAPI:
    settings = config.get_settings()
    app = FastAPI(title="ManobalAI", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router)
    app.include_router(chat_router.router)
    app.include_router(emotion_router.router)
    app.include_router(quotes_router.router)
    return app


app = create_app()