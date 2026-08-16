"""NEXUS Backend — FastAPI Application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger = logging.getLogger("nexus")
    logger.info("🔬 NEXUS — AI Research Scientist starting...")
    logger.info(f"   Demo Mode: {settings.demo_mode}")
    logger.info(f"   Gemini configured: {bool(settings.gemini_api_key)}")
    settings.ensure_directories()
    yield
    logger.info("NEXUS shutting down")


app = FastAPI(
    title="NEXUS — AI Research Scientist",
    description="Autonomous evidence-driven research agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
