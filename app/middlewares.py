from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import aiofiles
from app.data_files import UserData






class UserCheck(BaseMiddleware):

    async def __call__(self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any])->Any:


        current_users:set=data['current_users']
        if not event.from_user.id in current_users:
            users = set()
            async with aiofiles.open('allowed_users.txt', 'r') as f:
                async for line in f:
                    users.add(int(line))
            if event.from_user.id in users:
                current_users.add(event.from_user.id)
                await data['state'].set_data({'data': UserData()})
                return await handler(event, data)

            else:
                return
        else:
            return await handler(event, data)





