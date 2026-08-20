"""The `/api` router: individual endpoint modules mount onto this."""

from fastapi import APIRouter

from app.api.companies import router as companies_router
from app.api.contacts import router as contacts_router
from app.api.digest import router as digest_router
from app.api.health import router as health_router
from app.api.quota import router as quota_router
from app.api.threads import router as threads_router

router = APIRouter()
router.include_router(health_router)
router.include_router(companies_router)
router.include_router(contacts_router)
router.include_router(threads_router)
router.include_router(digest_router)
router.include_router(quota_router)
