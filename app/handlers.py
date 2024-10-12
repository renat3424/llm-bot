import os
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
import aiohttp
import io
import base64

from aiogram.fsm.context import  FSMContext
from app.llms import send_question, image_processing
from app.middlewares import UserCheck
from app.data_files import AppData, UserData
import app.keyboards as kb



router=Router()
router.message.middleware(UserCheck())
router.callback_query.middleware(UserCheck())
app_data=AppData()


def split_message(msg: str,  with_photo: bool) -> list[str]:

    parts = []
    while msg:

        if parts:
            max_msg_length = 4096
        elif with_photo:
            max_msg_length = 1024
        else:
            max_msg_length = 4096

        if len(msg) <= max_msg_length:

            parts.append(msg)
            break


        part = msg[:max_msg_length]
        first_ln = part.rfind("\n")

        if first_ln != -1:

            new_part = part[:first_ln]
            parts.append(new_part)


            msg = msg[first_ln + 1:]
            continue


        first_space = part.rfind(" ")

        if first_space != -1:

            new_part = part[:first_space]
            parts.append(new_part)


            msg = msg[first_space + 1:]
            continue


        parts.append(part)
        msg = msg[max_msg_length:]

    return parts


@router.message(CommandStart())
async def cmd_start(message:Message):




        text=('Добро пожаловать!\n\n'
              'Для выбора модели нажмите кнопку Выбрать модель.\n'
              f'По умолчанию модель для обработки текста: {app_data.default_text_model}\n'
              f'Для обработки изображений по умолчанию выбрана модель: {app_data.default_vision_model}\n'
              f'Чтобы выбрать помошь вызовете команду /help\n'
              f'Можете задавать свой вопрос:\n')


        await message.answer(text, reply_markup=kb.main)

@router.message(Command('help'))
async def show_models(message:Message):
    text = ('Для того, чтобы выбрать модель нажмите на кнопку Выбрать модель\n'
            'Для того, чтобы спросить языковую модель вопрос, введите модель в поле для ввода\n'
            'Для того, чтобы получить описание картинки отправьте картинку в чат\n'
            'Для того, чтобы получить ответ на вопрос о картинке отправьте картинку в чат и введите свой вопрос в поле Caption\n'
            'Для того, чтобы получить ответ на вопрос об уже отправленной картинке введите /image ...свой вопрос без точек... \n'
            'Полный список команд представлен ниже: \n\n\n'
            '/help-вызов помощи\n'
            '/models-получения списка доступных моделей\n'
            '/clear_history-удаление контекста сообщений, языковой модели станут неизвестны предыдущие сообщения\n'
            '/current_model-языковая модель выбранная на данный момент\n'
            '/image текст вопроса-задать вопрос по уже отправленной в чат последней картинке\n'
            )

    await message.answer(text, reply_markup=kb.main)

@router.message(Command('models'))
async def show_models(message:Message, available_models):
    try:

        text = ('На данный момент список доступных моделей включает в себя следующие модели:\n\n\n')

        for model in available_models:
            text += (f'Модель: {model["id"]}\n'
                     f'Кого: {model["by"]}\n\n')

        await message.answer(text, reply_markup=kb.main)
    except Exception as e:
        await message.answer(str(e), reply_markup=kb.main)

@router.message(F.text=='Выбрать модель')
async def choose_model(message: Message, available_models):

    keyboard=await kb.inline_models(available_models)
    await message.answer('Выберите модель', reply_markup=keyboard)


@router.callback_query(F.data.startswith('model_'))
async def get_model(call: CallbackQuery, state:FSMContext):
    user_data = await state.get_data()

    user_data = user_data['data']
    model=call.data.split('_')[1]

    user_data.chosen_model=None if model=="default" else model
    await state.set_data({'data': user_data})
    await call.answer(f'Модель {model}')
    await call.message.answer(f'Вы выбрали модель {"по умолчанию "+app_data.default_text_model if model=="default" else model}', reply_markup=kb.main)






@router.message(Command("clear_history"))
async def clear_user_history(message: Message, state:FSMContext):
    user_data=await state.get_data()
    user_data=user_data['data']
    user_data.user_history=user_data.user_history[:1]
    await state.set_data({'data': user_data})
    await message.answer('Контекст удален. Предыдущие сообщения не учитываются.', reply_markup=kb.main)


@router.message(Command("image"))
async def image_answer(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_data = user_data['data']
    photo=user_data.previous_image
    if photo==None:
        await message.answer('Пожалуйста отправьте фото')
    text=message.text.split('/image')[1].strip()
    if text=='':
        await message.answer('Пожалуйста отправьте сообщение')
    current_model = user_data.chosen_model if user_data.chosen_model in app_data.known_vision_models else app_data.default_vision_model

    response = await image_processing(text, photo, current_model)

    if '!Exception:' in response:

        await message.answer(response, reply_markup=kb.main)
    else:
        parts=split_message(response, with_photo=False)
        for part in parts:
            await message.answer(part, reply_markup=kb.main)

@router.message(Command("current_model"))
async def clear_user_history(message: Message, state: FSMContext):
    user_data=await state.get_data()
    user_data=user_data['data']
    if user_data.chosen_model is None:
        await message.answer(f'Текущая модель-модель по умолчанию {app_data.default_text_model}', reply_markup=kb.main)
    else:
        await message.answer(f'Текущая модель {user_data.chosen_model}', reply_markup=kb.main)

@router.message(F.text)
async def getting_text(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_data = user_data['data']
    if len(user_data.user_history)>app_data.history_size:
        user_data.user_history=user_data.user_history[:1]+user_data.user_history[-6:]
    user_data.user_history.append({"role": "user", "content": message.text})
    current_model=user_data.chosen_model if user_data.chosen_model is not None else app_data.default_text_model

    response=await send_question(user_data.user_history, current_model)
    if '!Exception:' in response:

        await message.answer(response, reply_markup=kb.main)
    else:
        user_data.user_history.append({"role": "assistant", "content": response})
        await state.set_data({'data': user_data})
        parts = split_message(response, with_photo=False)
        for part in parts:
            await message.answer(part, reply_markup=kb.main)





@router.message(F.photo)
async def getting_photo(message: Message, bot: Bot, state: FSMContext):
    fp=io.BytesIO()
    await bot.download(file=message.photo[-1].file_id, destination=fp)
    photo=base64.b64encode(fp.read()).decode('utf-8')
    fp.close()
    user_data = await state.get_data()
    user_data = user_data['data']

    current_model=user_data.chosen_model if user_data.chosen_model in app_data.known_vision_models else app_data.default_vision_model

    response=await image_processing(message.caption, photo, current_model)

    if '!Exception:' in response:

        await message.answer(response, reply_markup=kb.main)
    else:

        user_data.previous_image = photo
        await state.set_data({'data': user_data})
        parts=split_message(response, with_photo=False)
        for part in parts:
            await message.answer(part, reply_markup=kb.main)


