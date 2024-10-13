import asyncio
import os
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from app.handlers import router
from app.llms import get_models


async def main():
    bot=Bot(token=os.getenv('TOKEN'))
    storage=MemoryStorage()
    dispatcher=Dispatcher(storage=storage)
    dispatcher.include_router(router)
    available_models=await get_models()
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot, current_users=set(), available_models=available_models)


if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
