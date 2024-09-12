from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import User
import logging


def keyboard_registration() -> InlineKeyboardMarkup:
    logging.info("keyboard_registration")
    button_1 = InlineKeyboardButton(text='Регистрация', callback_data=f'registration')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]],)
    return keyboard


def keyboard_user_info(user_info: User) -> InlineKeyboardMarkup:
    logging.info(f"keyboard_user_info")
    if user_info.fullname == 'default':
        fullname = ''
    else:
        fullname = user_info.fullname
    button_1 = InlineKeyboardButton(text=f'ФИО: {fullname}', callback_data=f'fullname')
    if user_info.job == 'default':
        job = ''
    else:
        job = user_info.job
    button_2 = InlineKeyboardButton(text=f'Должность: {job}', callback_data=f'job')
    if user_info.power == 'default':
        power = ''
    else:
        power = user_info.power
    button_3 = InlineKeyboardButton(text=f'Мощность: {power}', callback_data=f'power')
    if user_info.district == 'default':
        district = ''
    else:
        district = user_info.district
    button_4 = InlineKeyboardButton(text=f'Участок: {district}', callback_data=f'district')
    button_5 = InlineKeyboardButton(text=f'Отменить ❌', callback_data=f'cancel_user_info')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4], [button_5]],)
    return keyboard


def keyboard_position(list_position: list) -> InlineKeyboardMarkup:
    logging.info(f"keyboards_attach_resources")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for position in list_position:
        text = position
        button = f'select_{position}'
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=button))
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()


def keyboard_user_full(user_info: User) -> InlineKeyboardMarkup:
    logging.info(f"keyboard_user_full")
    button_1 = InlineKeyboardButton(text=f'ФИО: {user_info.fullname}', callback_data=f'fullname')
    button_2 = InlineKeyboardButton(text=f'Должность: {user_info.job}', callback_data=f'job')
    button_3 = InlineKeyboardButton(text=f'Мощность: {user_info.power}', callback_data=f'power')
    button_4 = InlineKeyboardButton(text=f'Участок: {user_info.district}', callback_data=f'district')
    button_5 = InlineKeyboardButton(text=f'Зарегистрироваться', callback_data=f'registration_full')
    button_6 = InlineKeyboardButton(text=f'Отменить ❌', callback_data=f'cancel_user_info')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4], [button_5], [button_6]],)
    return keyboard


def keyboard_moderation(tg_user: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_moderation")
    button_1 = InlineKeyboardButton(text='Принять', callback_data=f'moderation_yes_{tg_user}')
    button_2 = InlineKeyboardButton(text='Отклонить', callback_data=f'moderation_no_{tg_user}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]],)
    return keyboard
