import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.ai import router as ai_router
from app.api.routes.health import router as health_router
from app.api.routes.monitor import router as monitor_router
from app.api.routes.profile import router as profile_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import DatabaseNotConfigured
from app.services.ai.ollama import OllamaError

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(monitor_router, prefix="/api/v1")
artwork_directory = settings.data_dir / "artworks"
artwork_directory.mkdir(parents=True, exist_ok=True)
app.mount("/media/artworks", StaticFiles(directory=artwork_directory), name="artworks")


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(DatabaseNotConfigured)
async def database_config_error_handler(
    request: Request, exc: DatabaseNotConfigured
) -> JSONResponse:
    logger.warning("Database configuration required for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database operation failed for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "Banco indisponível. Confira DATABASE_URL e o serviço PostgreSQL."},
    )


@app.exception_handler(OllamaError)
async def ollama_error_handler(request: Request, exc: OllamaError) -> JSONResponse:
    logger.warning(
        "Local model integration unavailable for %s %s: %s", request.method, request.url.path, exc
    )
    return JSONResponse(status_code=503, content={"detail": str(exc)})
