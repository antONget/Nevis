import asyncio
import time

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.googlesheets import append_row
from config_data.config import Config, load_config
import database.requests as rq
import keyboards.keyboard_report as kb
from services.googlesheets import get_list_all_rows
import logging


router = Router()
config: Config = load_config()


class Change(StatesGroup):
    number_order = State()
    part_designation = State()
    part_title = State()
    data_create = State()
    data_complete = State()
    count_part = State()
    count_defect = State()
    reason_defect = State()


async def user_text(tg_id: int) -> str:
    """
    Функция для формирования сведений об исполнителе
    :param tg_id:
    :return:
    """
    logging.info("user_text")
    user = await rq.get_user_tg_id(tg_id=tg_id)
    text = f'<b>ID:</b> {user.tg_id}\n' \
           f'<b>ФИО:</b> {user.fullname}\n' \
           f'<b>Должность:</b> {user.job}\n' \
           f'<b>Участок:</b> {user.district}\n\n'
    return text


async def report_text(report_id, report_data: list) -> str:
    """
    Функция для формирования текста отчета
    :param report_id:
    :param report_data:
    :return:
    """
    logging.info(f"report_text")
    report_info = await rq.get_report(report_id=report_id)
    text = ''
    for data in report_data:
        if data == 'number_order':
            text += f'<b>Номер заказа:</b> {report_info.number_order}\n'
        if data == 'part_designation':
            text += f'<b>Обозначение детали:</b> {report_info.part_designation}\n'
        if data == 'part_title':
            text += f'<b>Наименование детали:</b> {report_info.part_title}\n'
        if data == 'title_action':
            text += f'<b>Название операции:</b> {report_info.title_action}\n'
        if data == 'description_action':
            text += f'<b>Описание операции:</b> {report_info.description_action}\n'
        if data == 'title_machine':
            text += f'<b>Название станка:</b> {report_info.title_machine}\n'
        if data == 'machine_time':
            text += f'<b>Машинное время:</b> {report_info.machine_time}\n'
        if data == 'count_part':
            text += f'<b>Количество деталей:</b> {report_info.count_part}\n'
        if data == 'is_all_installed':
            text += f'<b>Все ли детали установлены:</b> {report_info.is_all_installed}\n'
        if data == 'is_defect':
            text += f'<b>Есть брак:</b> {report_info.is_defect}\n'
        if data == 'count_defect':
            text += f'<b>Количество брака:</b> {report_info.count_defect}\n'
        if data == 'reason_defect':
            text += f'<b>Причина брака:</b> {report_info.reason_defect}\n'
        if data == 'count_machine':
            text += f'<b>Работа на 1-м или 2-х станках:</b> {report_info.count_machine}\n'
        if data == 'data_create':
            text += f'<b>Время начала изготовления:</b> {":".join(report_info.data_create.split("/")[:3])}\n'
        if data == 'data_complete':
            text += f'<b>Время окончания изготовления:</b> {":".join(report_info.data_complete.split("/")[:3])}\n'
        if data == 'note_report':
            text += f'<b>Примечание:</b> {report_info.note_report}\n'
    text += '\n'
    return text


async def check_report_change(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Функция для отображения отчета для проверки и правки
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'check_report {message.chat.id}')
    data = await state.get_data()
    report_id = data['report_id']
    report_info = await rq.get_report(report_id=report_id)
    text_user = await user_text(tg_id=message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'machine_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'reason_defect',
                                                 'note_report',
                                                 'data_create',
                                                 'data_complete'])
    try:
        await bot.edit_message_caption(
            caption=f'{text_user}{text_report}',
            chat_id=message.chat.id,
            message_id=data['check_message'],
            reply_markup=kb.keyboard_change_report(info_report=report_info))
    except:
        await bot.edit_message_caption(
            caption=f'{text_user}{text_report}.',
            chat_id=message.chat.id,
            message_id=data['check_message'],
            reply_markup=kb.keyboard_change_report(info_report=report_info))


@router.callback_query(F.data == 'change_report-number_order')
async def select_change_number_order(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение номера заказа
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_number_order {callback.message.chat.id}")
    await callback.message.answer(text=f'Пришлите номер заказа')
    await state.set_state(Change.number_order)
    await callback.answer()


@router.message(F.text, StateFilter(Change.number_order))
async def process_get_number_order(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем номер заказа
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_number_order {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"number_order": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-title_action')
async def select_change_title_action(callback: CallbackQuery, bot: Bot, state: FSMContext) -> None:
    """
    Изменение названия операции
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_title_action {callback.message.chat.id}")
    list_title_action = await get_list_all_rows(data='action')
    data = await state.get_data()
    await bot.edit_message_caption(
        caption=f'Выберите название операции:',
        chat_id=callback.message.chat.id,
        message_id=data['check_message'],
        reply_markup=kb.keyboard_select_report(list_report=list_title_action,
                                               callback_report='change_action'))
    await callback.answer()


@router.callback_query(F.data.startswith('change_action'))
async def change_title_action(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обработка изменения названия операции
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"change_title_action {callback.message.chat.id}")
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"title_action": callback.data.split('_')[-1]})
    await check_report_change(message=callback.message, state=state, bot=bot)
    await callback.answer()


@router.callback_query(F.data == 'change_report-part_designation')
async def select_change_part_designation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Изменение обозначения детали
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_part_designation {callback.message.chat.id}")
    await callback.message.answer(text=f'Пришлите обозначение детали')
    await state.set_state(Change.part_designation)
    await callback.answer()


@router.message(F.text, StateFilter(Change.part_designation))
async def process_get_part_designation(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем номер заказа
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_part_designation {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"part_designation": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-part_title')
async def select_change_part_title(callback: CallbackQuery, state: FSMContext):
    """
    Изменение наименования детали
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_part_title {callback.message.chat.id}")
    await callback.message.answer(text=f'Пришлите наименование детали')
    await state.set_state(Change.part_title)
    await callback.answer()


@router.message(F.text, StateFilter(Change.part_title))
async def process_get_part_title(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем наименование детали
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_part_title {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"part_title": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-data_create')
async def select_change_data_create(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение времени начала работы
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_data_create {callback.message.chat.id}")
    await callback.message.answer(text=f'Пришлите время начала работы')
    await state.set_state(Change.data_create)
    await callback.answer()


@router.message(F.text, StateFilter(Change.data_create))
async def process_get_data_create(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем время начала работы
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_data_create {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"data_create": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-data_complete')
async def select_change_data_complete(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение времени начала работы
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_data_complete {callback.message.chat.id}")
    await callback.message.answer(text=f'Пришлите время окончания работы')
    await state.set_state(Change.data_complete)
    await callback.answer()


@router.message(F.text, StateFilter(Change.data_complete))
async def process_get_data_complete(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем время окончания работы
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_data_complete {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"data_complete": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-count_part')
async def select_change_count_part(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение времени начала работы
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_count_part {callback.message.chat.id}")
    await callback.message.answer(text=f'Количество деталей')
    await state.set_state(Change.count_part)
    await callback.answer()


@router.message(F.text, StateFilter(Change.count_part))
async def process_get_count_part(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем количество деталей
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_count_part {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"count_part": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-reason_defect')
async def select_change_reason_defect(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение времени начала работы
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_reason_defect {callback.message.chat.id}")
    await callback.message.answer(text=f'Причина брака')
    await state.set_state(Change.reason_defect)
    await callback.answer()


@router.message(F.text, StateFilter(Change.reason_defect))
async def process_get_reason_defect(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем причину брака
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_reason_defect {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"reason_defect": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.callback_query(F.data == 'change_report-description_action')
async def select_change_description_action(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Изменение описания операции
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_description_action {callback.message.chat.id}")
    list_title_action = await get_list_all_rows(data='operation')
    data = await state.get_data()
    await bot.edit_message_caption(
        caption=f'Выберите описание операции:',
        chat_id=callback.message.chat.id,
        message_id=data['check_message'],
        reply_markup=kb.keyboard_select_report(list_report=list_title_action,
                                               callback_report='change_operation'))
    await callback.answer()


@router.callback_query(F.data.startswith('change_operation'))
async def change_operation(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Изменение описания операции
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"change_operation {callback.message.chat.id}")
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"description_action": callback.data.split('_')[-1]})
    await check_report_change(message=callback.message, state=state, bot=bot)
    await callback.answer()


@router.callback_query(F.data == 'change_report-title_machine')
async def select_change_title_machine(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Выбор названия станка
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_title_machine {callback.message.chat.id}")
    list_title_action = await get_list_all_rows(data='title_machine')
    data = await state.get_data()
    await bot.edit_message_caption(
        caption=f'Выберите название станка:',
        chat_id=callback.message.chat.id,
        message_id=data['check_message'],
        reply_markup=kb.keyboard_select_report(list_report=list_title_action,
                                               callback_report='change_title_machine'))
    await callback.answer()


@router.callback_query(F.data.startswith('change_title_machine'))
async def change_title_machine(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Изменение названия станка
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"change_title_action {callback.message.chat.id}")
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"title_machine": callback.data.split('_')[-1]})
    await check_report_change(message=callback.message, state=state, bot=bot)
    await callback.answer()


@router.callback_query(F.data == 'change_report-is_all_installed')
async def select_change_is_all_installed(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Изменение значение установки всех деталей
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_is_all_installed {callback.message.chat.id}")
    data = await state.get_data()
    report_id = data['report_id']
    report = await rq.get_report(report_id=report_id)
    input_ = 'Да'
    if report.is_all_installed == 'Да':
        input_ = 'Heт'
    await rq.set_report(report_id=report_id,
                        data={"is_all_installed": input_})
    await check_report_change(message=callback.message, state=state, bot=bot)
    await callback.answer()


@router.callback_query(F.data == 'change_report-is_defect')
async def select_change_is_defect(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Изменение наличия брака
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_is_defect {callback.message.chat.id}")
    data = await state.get_data()
    report_id = data['report_id']
    report = await rq.get_report(report_id=report_id)
    if report.is_defect == 'Да':
        is_defect = 'Heт'
    else:
        is_defect = 'Да'
    await rq.set_report(report_id=report_id,
                        data={"is_defect": is_defect})
    await check_report_change(message=callback.message, state=state, bot=bot)
    await callback.answer()


@router.callback_query(F.data == 'change_report-count_machine')
async def select_change_count_machine(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Изменение количества станков
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"select_change_count_machine {callback.message.chat.id}")
    data = await state.get_data()
    report_id = data['report_id']
    report = await rq.get_report(report_id=report_id)
    if report.count_machine == '1':
        count_machine = '2'
    else:
        count_machine = '1'
    await rq.set_report(report_id=report_id,
                        data={"count_machine": count_machine})
    await check_report_change(message=callback.message, state=state, bot=bot)
    await callback.answer()


@router.callback_query(F.data == 'change_report-count_defect')
async def select_change_count_defect(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Изменение количества брака
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"select_change_count_defect {callback.message.chat.id}")
    await callback.message.answer(text=f'Количество брака')
    await state.set_state(Change.count_defect)
    await callback.answer()


@router.message(F.text, StateFilter(Change.count_defect))
async def process_get_count_defect(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем количество дефектов
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_get_count_defect {message.chat.id}")
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"count_defect": message.text})
    await state.set_state(state=None)
    await check_report_change(message=message, state=state, bot=bot)


@router.message(F.text == 'Подтвердить отчет')
async def confirm_report(message: Message, state: FSMContext, bot: Bot):
    """
    Подтверждение отчета
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('confirm_report')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    data = await state.get_data()
    report_id = data['report_id']
    info_order = await rq.get_report(report_id=report_id)
    list_order = [info_order.number_order,
                  info_order.part_designation,
                  info_order.title_action,
                  info_order.part_title,
                  info_order.description_action,
                  info_order.title_machine,
                  info_order.machine_time,
                  info_order.count_part,
                  info_order.is_all_installed,
                  info_order.is_defect,
                  info_order.count_defect,
                  info_order.reason_defect,
                  info_order.note_report,
                  info_order.data_create,
                  info_order.data_complete]
    text = "Админу отправляем отчет?"
    await append_row(data=list_order)
    await message.answer(text='Отчет отправлен в гугл таблицу',
                         reply_markup=kb.keyboard_report_start())
    await rq.set_report(report_id=report_id,
                        data={"status": rq.ReportStatus.complied})
    for admin in config.tg_bot.admin_ids.split(','):
        try:
            await bot.send_message(chat_id=admin,
                                   text=text)
        except:
            pass


@router.message(F.text == 'Отменить отчет')
async def cancel_report(message: Message, bot: Bot):
    """
    Отмена отправки отчета
    :param message:
    :param bot:
    :return:
    """
    logging.info('cancel_report')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await message.answer(text='Добавление отчета отменено',
                         reply_markup=kb.keyboard_report_start())
