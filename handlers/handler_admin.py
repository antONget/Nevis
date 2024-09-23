from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest

import keyboards.keyboard_admin as kb
import database.requests as rq
from filter.admin_filter import IsSuperAdmin
from config_data.config import Config, load_config
from secrets import token_urlsafe

import logging

config: Config = load_config()
router = Router()
user_dict = {}


@router.callback_query(lambda callback: 'moderation' in callback.data)
async def moderation_user(callback: CallbackQuery, bot: Bot):
    """
    Модерация регистрации пользователя
    :param callback:
    :param bot:
    :return:
    """
    logging.info(f'moderation_user: {callback.message.chat.id}')
    answer = callback.data.split('_')[1]
    if answer == 'yes':
        user_info = await rq.get_user_tg_id(tg_id=int(callback.data.split('_')[2]))
        await callback.answer(text=f'Пользователь @{user_info.username} авторизован в боте')
        user = await rq.get_user_tg_id(tg_id=int(callback.data.split('_')[2]))
        await bot.send_message(chat_id=callback.data.split('_')[2],
                               text=f'<b>ID:</b> {user.tg_id}\n'
                                    f'<b>ФИО:</b> {user.fullname}\n'
                                    f'<b>Должность:</b> {user.job}\n'
                                    f'<b>Участок:</b> {user.district}\n\n'
                                    f'Выберите раздел',
                               reply_markup=kb.keyboard_user_mode())
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=callback.message.message_id)
        await callback.answer(text='Пользователь успешно авторизован в боте')
    await callback.answer()


# Персонал
@router.message(F.text == 'Панель управления', IsSuperAdmin())
async def admin_mode_chapter(message: Message) -> None:
    """
    Нажата кнопка "Панель управления"
    :param message:
    :return:
    """
    logging.info(f'admin_mode_chapter: {message.chat.id}')
    await message.answer(text='Выберите действие!',
                         reply_markup=kb.keyboard_admin_mode())








