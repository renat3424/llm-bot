from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

main=ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Выбрать модель')]], resize_keyboard=True
)
async def inline_models(available_models):
    keyboard=InlineKeyboardBuilder()
    for model in available_models:
        keyboard.add(InlineKeyboardButton(text=model["id"], callback_data=f"model_{model['id']}"))
    keyboard.add(InlineKeyboardButton(text='По умолчанию', callback_data='model_default'))
    return keyboard.adjust(2).as_markup()



