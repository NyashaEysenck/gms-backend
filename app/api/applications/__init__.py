from fastapi import APIRouter
from .core import router as core_router
from .reviews import router as reviews_router
from .signoff import router as signoff_router
from .documents import router as documents_router

# Main applications router
router = APIRouter(prefix="/applications", tags=["applications"])

# Include all sub-routers
router.include_router(core_router)
router.include_router(reviews_router)
router.include_router(signoff_router)
router.include_router(documents_router)
