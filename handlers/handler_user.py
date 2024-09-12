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


class Registration(StatesGroup):
    fullname = State()


@router.message(F.text == 'Мой профиль')
@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Запуск бота - нажата кнопка "Начать" или введена команда "/start"
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_start_command {message.chat.id}")
    await state.set_state(default_state)
    user = await rq.get_user_tg_id(tg_id=message.chat.id)
    if not user:
        await rq.add_user(tg_id=message.chat.id,
                          data={"tg_id": message.chat.id, "username": message.from_user.username})
        await message.answer(text=f'Пожалуйста, пройдите процедуру регистрации',
                             reply_markup=kb.keyboard_registration())
    else:
        if user.fullname == 'default':
            fullname = ''
        else:
            fullname = user.fullname
        if user.job == 'default':
            job = ''
        else:
            job = user.job
        if user.power == 'default':
            power = ''
        else:
            power = user.power
        if user.district == 'default':
            district = ''
        else:
            district = user.district
        try:
            data = await state.get_data()
            msg = data['msg']
            await bot.edit_message_text(chat_id=message.chat.id,
                                        text=f'<b>ID:</b> {user.tg_id}\n'
                                             f'<b>ФИО:</b> {fullname}\n'
                                             f'<b>Должность:</b> {job}\n'
                                             f'<b>Мощность:</b> {power}\n'
                                             f'<b>Участок:</b> {district}\n\n'
                                             f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                        message_id=msg,
                                        reply_markup=kb.keyboard_user_info(user_info=user))
        except:
            msg = await message.answer(text=f'<b>ID:</b> {user.tg_id}\n'
                                            f'<b>ФИО:</b> {fullname}\n'
                                            f'<b>Должность:</b> {job}\n'
                                            f'<b>Мощность:</b> {power}\n'
                                            f'<b>Участок:</b> {district}\n\n'
                                            f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                       reply_markup=kb.keyboard_user_info(user_info=user))
            await state.update_data(msg=msg.message_id)


@router.callback_query(F.data == 'registration')
async def process_registration(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Регистрация пользователя
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_registration {callback.message.chat.id}")
    user_info = await rq.get_user_tg_id(tg_id=callback.message.chat.id)
    if user_info.fullname == 'default':
        fullname = ''
    else:
        fullname = user_info.fullname
    if user_info.job == 'default':
        job = ''
    else:
        job = user_info.job
    if user_info.power == 'default':
        power = ''
    else:
        power = user_info.power
    if user_info.district == 'default':
        district = ''
    else:
        district = user_info.district
    try:
        data = await state.get_data()
        msg = data['msg']
        await bot.edit_message_text(chat_id=callback.message.chat.id,
                                    text=f'<b>ID:</b> {user_info.tg_id}\n'
                                         f'<b>ФИО:</b> {fullname}\n'
                                         f'<b>Должность:</b> {job}\n'
                                         f'<b>Мощность:</b> {power}\n'
                                         f'<b>Участок:</b> {district}\n\n'
                                         f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                    message_id=msg,
                                    reply_markup=kb.keyboard_user_info(user_info=user_info))
    except:
        msg = await callback.message.answer(text=f'<b>ID:</b> {user_info.tg_id}\n'
                                                 f'<b>ФИО:</b> {fullname}\n'
                                                 f'<b>Должность:</b> {job}\n'
                                                 f'<b>Мощность:</b> {power}\n'
                                                 f'<b>Участок:</b> {district}\n\n'
                                                 f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                            reply_markup=kb.keyboard_user_info(user_info=user_info))
        await state.update_data(msg=msg.message_id)


@router.callback_query(F.data == 'fullname')
async def change_fullname(callback: CallbackQuery, state: FSMContext):
    """
    Добавление/Изменение ФИО
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'change_fullname {callback.message.chat.id}')
    await callback.message.answer(text=f'Введите Фамилию Имя Отчество')
    await state.update_data(full_name=1)
    await state.set_state(Registration.fullname)
    await callback.answer()


@router.message(F.text, StateFilter(Registration.fullname))
async def get_fullname(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем от пользователя ФИО
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_fullname {message.chat.id}')
    await rq.set_fullname(fullname=message.html_text, tg_id=message.chat.id)
    await state.set_state(default_state)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-1)
    if await rq.check_registration(tg_id=message.chat.id):
        await registration_full(message=message, state=state, bot=bot)
    else:
        await process_start_command(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'job')
@router.callback_query(F.data == 'power')
@router.callback_query(F.data == 'district')
async def select_change_job(callback: CallbackQuery, state: FSMContext):
    """
    Обновление должности/мощности/участка пользователя
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'select_change_job {callback.message.chat.id}')
    list_position = await get_list_all_rows(data=callback.data)
    user_info = await rq.get_user_tg_id(tg_id=callback.message.chat.id)
    await state.update_data(type_position=callback.data)
    await state.update_data(full_name=0)
    if user_info.fullname == 'default':
        fullname = ''
    else:
        fullname = user_info.fullname
    if user_info.job == 'default':
        job = ''
    else:
        job = user_info.job
    if user_info.power == 'default':
        power = ''
    else:
        power = user_info.power
    if user_info.district == 'default':
        district = ''
    else:
        district = user_info.district
    await callback.message.edit_text(text=f'<b>ID:</b> {user_info.tg_id}\n'
                                          f'<b>ФИО:</b> {fullname}\n'
                                          f'<b>Должность:</b> {job}\n'
                                          f'<b>Мощность:</b> {power}\n'
                                          f'<b>Участок:</b> {district}\n\n'
                                          f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                     reply_markup=kb.keyboard_position(list_position=list_position))
    await callback.answer()


@router.callback_query(F.data.startswith('select_'))
async def select_position(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Выбор позиции пользователя
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'select_position {callback.message.chat.id}')
    data = await state.get_data()
    type_position = data['type_position']
    position = callback.data.split('_')[1]
    if type_position == 'job':
        await rq.set_job(job=position, tg_id=callback.message.chat.id)
    elif type_position == 'power':
        await rq.set_power(power=position, tg_id=callback.message.chat.id)
    elif type_position == 'district':
        await rq.set_district(district=position, tg_id=callback.message.chat.id)
    await callback.answer()
    if await rq.check_registration(tg_id=callback.message.chat.id):
        await registration_full(message=callback.message, state=state, bot=bot)
    else:
        await process_registration(callback=callback, state=state, bot=bot)


@router.callback_query(F.data == 'cancel_user_info')
async def cancel_action(callback: CallbackQuery, bot: Bot):
    """
    Отмена
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'cancel_action {callback.message.chat.id}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    await callback.answer()


async def registration_full(message: Message, state: FSMContext, bot: Bot):
    """
    Регистрация завершена
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'registration_full {message.chat.id}')
    user_info = await rq.get_user_tg_id(tg_id=message.chat.id)
    data = await state.get_data()
    full_name = data['full_name']
    msg = data['msg']
    if full_name:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    text=f'<b>ID:</b> {user_info.tg_id}\n'
                                         f'<b>ФИО:</b> {user_info.fullname}\n'
                                         f'<b>Должность:</b> {user_info.job}\n'
                                         f'<b>Мощность:</b> {user_info.power}\n'
                                         f'<b>Участок:</b> {user_info.district}\n\n'
                                         f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                    message_id=msg,
                                    reply_markup=kb.keyboard_user_full(user_info=user_info))
    else:
        await message.edit_text(text=f'<b>ID:</b> {user_info.tg_id}\n'
                                     f'<b>ФИО:</b> {user_info.fullname}\n'
                                     f'<b>Должность:</b> {user_info.job}\n'
                                     f'<b>Мощность:</b> {user_info.power}\n'
                                     f'<b>Участок:</b> {user_info.district}\n\n'
                                     f'⚠️ Если хотите завершить работу с профилем, нажмите кнопку отменить',
                                reply_markup=kb.keyboard_user_full(user_info=user_info))


@router.callback_query(F.data == 'registration_full')
async def registration_finish(callback: CallbackQuery, bot: Bot):
    """
    Регистрация завершена
    :param callback:
    :param bot:
    :return:
    """
    logging.info(f'registration_finish {callback.message.chat.id}')
    await callback.message.edit_text(text='Данные переданы на модерацию. Ожидайте решения',
                                     reply_markup=None)
    user_info = await rq.get_user_tg_id(tg_id=callback.message.chat.id)
    text = f'<b>Пользователь зарегистрировался в ботe:</b>\n\n' \
           f'<b>ID:</b> {user_info.tg_id}\n' \
           f'<b>ФИО:</b> {user_info.fullname}\n' \
           f'<b>Должность:</b> {user_info.job}\n' \
           f'<b>Мощность:</b> {user_info.power}\n' \
           f'<b>Участок:</b> {user_info.district}\n\n' \
           f'Примите или откажите в регистрации.'
    admin_list = config.tg_bot.admin_ids.split(',')
    for admin in admin_list:
        try:
            await bot.send_message(chat_id=admin,
                                   text=text,
                                   reply_markup=kb.keyboard_moderation(tg_user=callback.message.chat.id))
        except:
            pass
