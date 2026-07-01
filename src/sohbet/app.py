"""FastAPI uygulama fabrikası.

Başlangıçta backend'ler bir kez kurulur (modeller bağlantılar arası paylaşılır)
ve vektör koleksiyonu hazırlanır. Web istemcisi ``clients/web`` altından
statik olarak sunulur.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sohbet.backends.registry import build_backends
from sohbet.config import get_settings
from sohbet.logging import get_logger, setup_logging
from sohbet.transport.ws import router as ws_router

logger = get_logger("sohbet.app")

_WEB_DIR = Path(__file__).resolve().parents[2] / "clients" / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Sohbet başlatılıyor...")
    backends = build_backends(settings)
    try:
        await backends.vectordb.ensure_collection(backends.embedding.dim)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Vektör koleksiyonu hazırlanamadı (şimdilik yok sayıldı): %s", exc)
    app.state.settings = settings
    app.state.backends = backends
    logger.info("Hazır. WS: /ws")
    yield
    logger.info("Sohbet kapatılıyor.")


def create_app() -> FastAPI:
    app = FastAPI(title="Sohbet — Türkçe Sesli Asistan", lifespan=lifespan)
    app.include_router(ws_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    if _WEB_DIR.exists():
        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(str(_WEB_DIR / "index.html"))

        app.mount("/static", StaticFiles(directory=str(_WEB_DIR)), name="static")

    return app


app = create_app()
