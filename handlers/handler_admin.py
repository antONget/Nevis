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


@router.callback_query(F.data == 'moderation_yes_843554518')
@router.callback_query(F.data.startwith('moderation_'))
async def moderation_user(callback: CallbackQuery, bot: Bot):
    """
    Модерация регистрации пользователя
    :param callback:
    :return:
    """
    logging.info(f'moderation_user: {callback.message.chat.id}')
    answer = callback.data.split('_')[1]
    if answer == 'yes':
        user_info = await rq.get_user_tg_id(tg_id=int(callback.data.split('_')[2]))
        await callback.answer(text=f'Пользователь @{user_info.username} авторизован в боте')
        await bot.send_message(chat_id=callback.data.split('_')[2],
                               text=f'Вы авторизованы в боте',
                               reply_markup=kb.keyboard_user_mode())
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








