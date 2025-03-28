from aiogram import Router
from .current_schedule import router as current_router
from .full_search import router as full_search_router
from .quick_search import router as quick_search_router

router = Router()
router.include_router(current_router)
router.include_router(full_search_router)
router.include_router(quick_search_router)