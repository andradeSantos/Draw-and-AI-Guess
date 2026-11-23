"""Entrypoint da aplicação FastAPI com lifespan, CORS e carregamento único do modelo."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.database import init_db
from backend.app.ml_service.predictor import load_predictor
from backend.app.routers.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    app.state.predictor = load_predictor(settings)
    yield
    app.state.predictor = None


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Desenhe e a IA Adivinha — Museu Ciência Viva",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(api_router, prefix="/api", include_in_schema=False)
    return app


app = create_app()
