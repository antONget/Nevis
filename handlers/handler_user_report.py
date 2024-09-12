from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state

from config_data.config import Config, load_config
import database.requests as rq
import keyboards.keyboard_user as kb
from services.googlesheets import get_list_all_rows


import logging


router = Router()
config: Config = load_config()


class Report(StatesGroup):
    fullname = State()


@router.message(F.text == 'Мой профиль')
async def process_start_command(message: Message, state: FSMContext, bot: Bot) -> None:
    """

    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_start_command {message.chat.id}")