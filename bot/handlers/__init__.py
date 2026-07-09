from aiogram import Router

from . import start, topics, demo, settings, stats

router = Router(name="main")
router.include_router(start.router)
router.include_router(topics.router)
router.include_router(demo.router)
router.include_router(settings.router)
router.include_router(stats.router)
