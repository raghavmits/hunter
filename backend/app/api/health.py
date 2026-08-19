"""GET /api/health — reports the app is up. No database access (issue #2)."""

from fastapi import APIRouter

from app import APP_NAME, __version__

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"name": APP_NAME, "version": __version__}
