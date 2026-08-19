"""App factory: builds the FastAPI instance and mounts the API router."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import APP_NAME, __version__
from app.api import router as api_router

# Vite's default dev server origin. Single-user, localhost-only app (PLAN.md N2),
# so this is the only origin CORS ever needs to allow.
VITE_DEV_ORIGIN = "http://localhost:5173"


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=__version__)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[VITE_DEV_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
