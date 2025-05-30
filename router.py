from aiogram import Router

from handlers import photo_handler, start


router = Router()

router.include_router(photo_handler.router)
