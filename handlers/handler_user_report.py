import asyncio
import re
import time

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from services.googlesheets import get_list_all_rows
from config_data.config import Config, load_config
import database.requests as rq
import keyboards.keyboard_report as kb
from datetime import datetime
import cv2
import logging
import os
import re
router = Router()
config: Config = load_config()


class Report(StatesGroup):
    photo = State()
    QR = State()
    QR_2 = State()
    number_order = State()
    part_designation = State()
    number_MSK = State()
    part_title = State()
    count_part = State()
    count_defect = State()
    reason_defect = State()
    note_report = State()
    find_number_order = State()
    machine_time = State()


async def user_text(tg_id: int):
    """
    Формирование информации об исполнителе
    :param tg_id:
    :return:
    """
    user = await rq.get_user_tg_id(tg_id=tg_id)
    text = f'<b>ID:</b> {user.tg_id}\n' \
           f'<b>ФИО:</b> {user.fullname}\n' \
           f'<b>Должность:</b> {user.job}\n' \
           f'<b>Участок:</b> {user.district}\n\n'
    return text


async def report_text(report_id, report_data: list):
    """
    Формирование информации об отчете
    :param report_id:
    :param report_data:
    :return:
    """
    report_info = await rq.get_report(report_id=report_id)
    text = ''
    for data in report_data:
        if data == 'number_order':
            text += f'<b>Номер заказа:</b> {report_info.number_order}\n'
        if data == 'part_designation':
            text += f'<b>Обозначение детали:</b> {report_info.part_designation}\n'
        if data == 'number_MSK':
            text += f'<b>Номер детали по MSK:</b> {report_info.number_MSK}\n'
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
        if data == 'average_time':
            text += f'<b>Среднее время на деталь:</b> {report_info.average_time} мин.\n'
        if data == 'count_part':
            text += f'<b>Количество деталей:</b> {report_info.count_part}\n'
        if data == 'is_all_installed':
            text += f'<b>Все ли детали установлены:</b> {report_info.is_all_installed}\n'
        if data == 'is_defect':
            text += f'<b>Есть брак:</b> {report_info.is_defect}\n'
        if data == 'count_defect':
            text += f'<b>Количество брака:</b> {report_info.count_defect}\n'
        if data == 'reason_defect':
            text += f'<b>Причина брака:</b> {report_info.reason_defect if report_info.reason_defect != "none" else "Отсутствует"}\n'
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


@router.message(F.text == 'Создать отчет')
async def process_create_part(message: Message, state: FSMContext) -> None:
    """
    Начало изготовления детали, запрос фотографии
    :param message:
    :param state:

    :return:
    """
    logging.info(f"process_create_part {message.chat.id}")
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'Для начала отчета отправьте фотографию чертежа детали.'
                              f' Для добавления фотографии нажмите на 📎',
                         reply_markup=kb.keyboard_again_start())
    await state.set_state(Report.photo)


@router.message(F.photo, StateFilter(Report.photo))
async def process_get_photo(message: Message, state: FSMContext) -> None:
    """
    Получаем фотографию и запрашиваем QR от пользователя
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_photo {message.chat.id}")
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'Сфотографируйте QR для добавления данных в заказ. Для добавления QR нажмите на 📎')
    await state.set_state(Report.QR)


@router.message(F.photo, StateFilter(Report.QR))
async def process_get_qr(message: Message, state: FSMContext) -> None:
    """
    Получаем QR от пользователя, пробуем его распознать если удается предлагаем подтвердить
     данные иначе повторить попытку или ввести данные вручную
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_qr {message.chat.id}")
    qr_id = message.photo[-1].file_id
    file_path = f"data/{qr_id}.jpg"
    await message.bot.download(
        qr_id,
        destination=file_path
    )
    img_qrcode = cv2.imread(file_path)
    detector = cv2.QRCodeDetector()
    data, bbox, clear_qrcode = detector.detectAndDecode(img_qrcode)
    if data:
        data_qr = ''
        list_qr = []
        for _ in data.split("\n"):
            data_qr += f'<b>{_.split(":")[0]}:</b> {_.split(":")[1]}\n'
            list_qr.append(_.split(":")[1])
        await message.answer(text=f'QR распознан\n\n'
                                  f'{data_qr}',
                             reply_markup=kb.keyboard_confirm_recognize())
        await state.update_data(number_order=list_qr[0])
        await state.update_data(part_designation=list_qr[1])
        await state.update_data(part_title=list_qr[2])
    else:
        await message.answer(text='QR не распознан. Повторите попытку',
                             reply_markup=kb.keyboard_not_recognize())
    try:
        os.remove(file_path)
        logging.info(f'Файл {file_path} успешно удалён.')
    except FileNotFoundError:
        logging.error(f'Файл {file_path} не найден.')
    except PermissionError:
        logging.error(f'У вас нет разрешения на удаление файла {file_path}.')
    except Exception as e:
        logging.error(f'Произошла ошибка: {e}')
    await state.set_state(state=None)


@router.callback_query(F.data == 'qr_confirm')
async def confirm_qr(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Подтверждение данных зашитых в QR
    :param callback: 
    :param state:
    :param bot:
    :return: 
    """
    logging.info(f"confirm_qr {callback.message.chat.id}")
    data = await state.get_data()
    text_user = await user_text(tg_id=callback.message.chat.id)
    await callback.message.edit_text(text=f'{text_user}'
                                          f'<b>Номер заказа:</b> {data["number_order"]}\n'
                                          f'<b>Наименование детали:</b> {data["part_title"]}\n'
                                          f'<b>Обозначение детали:</b> {data["part_designation"]}\n\n'
                                          f'Укажите номер операции по МСК')
    await callback.answer()
    await state.set_state(Report.number_MSK)
    # await bot.delete_message(chat_id=callback.message.chat.id,
    #                          message_id=callback.message.message_id)
    # list_title_machine = await get_list_all_rows(data='title_machine')
    # await callback.message.edit_text(text=f'Выберите наименование станка:',
    #                                  reply_markup=kb.keyboard_select_report(list_report=list_title_machine,
    #                                                                         callback_report='tmachine'))
    # data = await state.get_data()
    # data_dict = {"photo_id": data['photo_id'],
    #              "number_order": data["number_order"],
    #              "part_designation": data["part_designation"],
    #              "part_title": data["part_title"],
    #              "data_create": datetime.today().strftime('%H/%M/%S/%d/%m/%Y'),
    #              "status": rq.ReportStatus.create}
    # report_id = await rq.add_report(data=data_dict)
    # await state.update_data(report_id=report_id)
    # text_user = await user_text(tg_id=callback.message.chat.id)
    # await callback.message.answer(text=f'{text_user}'
    #                                    f'<b>Номер заказа:</b> {data["number_order"]}\n'
    #                                    f'<b>Обозначение детали:</b> {data["part_designation"]}\n'
    #                                    f'<b>Наименование детали:</b> {data["part_title"]}\n'
    #                                    f'<b>Время начала изготовления:</b> {datetime.today().strftime("%H:%M:%S")}',
    #                               reply_markup=kb.keyboard_report_start())
    # await callback.answer(text='Отчет на изготовление детали успешно открыт, для завершения выберите пункт'
    #                            ' меню "Завершить отчет" в меню ниже. Если вы ее не видите разверните меню нажав'
    #                            ' на иконку с 4-мя кружками', show_alert=True)


@router.callback_query(F.data == 'qr_recognize')
async def qr_recognize(callback: CallbackQuery, state: FSMContext):
    """
    Повторить распознавание QR
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"qr_recognize {callback.message.chat.id}")
    text_user = await user_text(tg_id=callback.message.chat.id)
    await callback.message.edit_text(text=f'{text_user}'
                                          f'Сфотографируйте QR для добавления данных в заказ.'
                                          f' Для добавления QR нажмите на 📎')
    await state.set_state(Report.QR)
    await callback.answer()


@router.callback_query(F.data == 'qr_hand_input')
async def qr_hand_input(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Ввод первичных данных вручную
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"qr_hand_input {callback.message.chat.id}")
    text_user = await user_text(tg_id=callback.message.chat.id)
    # await bot.delete_message(chat_id=callback.message.chat.id,
    #                          message_id=callback.message.message_id)
    await callback.message.edit_text(text=f'{text_user} Пришлите номер заказа',
                                     reply_markup=None)
    await state.set_state(Report.number_order)
    await callback.answer()


@router.message(F.text == '🏠 Главное меню')
async def process_main_menu(message: Message, state: FSMContext) -> None:
    """
    Главное меню
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_main_menu {message.chat.id}")
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}',
                         reply_markup=kb.keyboard_report_start())
    await state.set_state(Report.photo)


@router.message(F.text == 'Заполнить отчет заново 🔄')
async def process_again_input(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Повторить ввод данных при создании отчета
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_again_input {message.chat.id}")
    # await bot.delete_message(chat_id=message.chat.id,
    #                          message_id=message.message_id - 1)
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'Для начала отчета отправьте фотографию чертежа детали.'
                              f' Для добавления фотографии нажмите на 📎',
                         reply_markup=kb.keyboard_again_start())
    await state.set_state(Report.photo)


@router.message(F.text == 'Зaполнить отчет зaново 🔄')
async def process_again_input_2(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Повторить ввод данных при завершении отчета
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_again_input_2 {message.chat.id}")
    # await message.answer(text=f'Пришлите фото QR-кода. Для добавления QR нажмите на 📎',
    #                      reply_markup=kb.keyboard_again_finish())
    # await state.set_state(Report.QR_2)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    reports = await rq.get_reports_creator_status(creator=message.chat.id, status=rq.ReportStatus.create)
    list_report = [report for report in reports]
    if not list_report:
        await message.answer(text='У вас нет открытых отчетов. чтобы открыть отчет нажмите "Создать отчет"')
        return

    await message.answer(text='Выберите отчет для его завершения',
                         reply_markup=kb.keyboard_select_report_complete(list_report=list_report,
                                                                         callback_report='comletereport'))


@router.message(F.text, StateFilter(Report.number_order))
async def process_get_number_order(message: Message, state: FSMContext) -> None:
    """
    Получаем номер заказа
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_number_order {message.chat.id}")
    await state.update_data(number_order=message.text)
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'<b>Номер заказа:</b> {message.text}\n\n'
                              f'Пришлите наименование детали')
    await state.set_state(Report.part_title)


@router.message(F.text, StateFilter(Report.part_title))
async def process_get_part_title(message: Message, state: FSMContext) -> None:
    """
    Получаем наименование детали
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_part_title {message.chat.id}")
    await state.update_data(part_title=message.text)
    data = await state.get_data()
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'<b>Номер заказа:</b> {data["number_order"]}\n'
                              f'<b>Наименование детали:</b> {message.text}\n\n'
                              f'Пришлите обозначение детали')
    await state.set_state(Report.part_designation)


@router.message(F.text, StateFilter(Report.part_designation))
async def process_get_part_designation(message: Message, state: FSMContext) -> None:
    """
    Получаем обозначение детали и выводим клавиатуру выбора названия станка
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_part_designation {message.chat.id}")
    await state.update_data(part_designation=message.text)
    # data = await state.get_data()
    # data_dict = {"photo_id": data['photo_id'],
    #              "number_order": data["number_order"],
    #              "part_designation": data["part_designation"],
    #              "part_title": data["part_title"],
    #              "data_create": datetime.today().strftime('%H/%M/%S/%d/%m/%Y'),
    #              "status": rq.ReportStatus.create}
    # report_id = await rq.add_report(data=data_dict)
    # time.sleep(0.1)
    # await state.update_data(report_id=report_id)
    # text_user = await user_text(tg_id=message.chat.id)
    # text_report = await report_text(report_id=report_id,
    #                                 report_data=['number_order', 'part_designation', 'part_title', 'data_create'])
    # await message.answer(text=f'{text_user}{text_report}'
    #                           f'Отчет на изготовление детали успешно открыт, для завершения выберите пункт'
    #                           ' меню "Завершить отчет"',
    #                      reply_markup=kb.keyboard_report_start())
    # await state.set_state(state=None)
    data = await state.get_data()
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'<b>Номер заказа:</b> {data["number_order"]}\n'
                              f'<b>Наименование детали:</b> {data["part_title"]}\n'
                              f'<b>Обозначение детали:</b> {message.text}\n\n'
                              f'Укажите номер операции по МСК')
    await state.set_state(Report.number_MSK)


@router.message(F.text, StateFilter(Report.number_MSK))
async def process_get_number_msk(message: Message, state: FSMContext) -> None:
    """
    Получаем номер детели по MSK
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_number_MSK {message.chat.id}")
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer(text='Номер операции по МСК должно быть целым числом, указанным цифрами')
        return
    await state.update_data(number_MSK=message.text)
    list_title_machine = await get_list_all_rows(data='title_machine')
    data = await state.get_data()
    text_user = await user_text(tg_id=message.chat.id)
    await message.answer(text=f'{text_user}'
                              f'<b>Номер заказа:</b> {data["number_order"]}\n'
                              f'<b>Наименование детали:</b> {data["part_title"]}\n'
                              f'<b>Обозначение детали:</b> {data["part_designation"]}\n'
                              f'<b>Номер операции по МСК:</b> {message.text}\n\n'
                              f'Выберите наименование станка из списка ниже:',
                         reply_markup=kb.keyboard_select_report(list_report=list_title_machine,
                                                                callback_report='tmachine'))


@router.callback_query(F.data.startswith('tmachine'))
async def process_select_description_operation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Получаем название станка
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f"process_select_description_operation {callback.message.chat.id}")
    # await bot.delete_message(chat_id=callback.message.chat.id,
    #                          message_id=callback.message.message_id)
    title_machine = callback.data.split('_')[-1]
    await state.update_data(title_machine=title_machine)
    list_title_action = await get_list_all_rows(data='action')
    data = await state.get_data()
    text_user = await user_text(tg_id=callback.message.chat.id)
    await callback.message.edit_text(text=f'{text_user}'
                                          f'<b>Номер заказа:</b> {data["number_order"]}\n'
                                          f'<b>Наименование детали:</b> {data["part_title"]}\n'
                                          f'<b>Обозначение детали:</b> {data["part_designation"]}\n'
                                          f'<b>Номер операции по МСК:</b> {data["number_MSK"]}\n'
                                          f'<b>Наименование станка:</b> {title_machine}\n\n'
                                          f'Выберите название операции:',
                                     reply_markup=kb.keyboard_select_report(list_report=list_title_action,
                                                                            callback_report='action'))
    await callback.answer()


@router.callback_query(F.data.startswith('action'))
async def process_select_title_action(callback: CallbackQuery, state: FSMContext):
    """
    Выбрать наименование операции
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'process_select_title_action {callback.message.chat.id}')
    title_action = callback.data.split('_')[-1]
    data = await state.get_data()
    data_dict = {"photo_id": data['photo_id'],
                 "creator": callback.message.chat.id,
                 "number_order": data["number_order"],
                 "part_designation": data["part_designation"],
                 "number_MSK": data["number_MSK"],
                 "part_title": data["part_title"],
                 "data_create": str(datetime.today().strftime('%H:%M:%S %d-%m-%Y')),
                 "title_machine": data["title_machine"],
                 "title_action": title_action,
                 "status": rq.ReportStatus.create}
    report_id = await rq.add_report(data=data_dict)
    time.sleep(0.1)
    await state.update_data(report_id=report_id)
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'part_title',
                                                 'title_machine',
                                                 'title_action',
                                                 'data_create'])
    await callback.message.edit_text(text=f'{text_user}{text_report}'
                                          f'Отчет на изготовление детали успешно открыт.',
                                     reply_markup=None)
    await callback.message.answer(text=f'Для завершения выберите пункт'
                                       f' меню "Завершить отчет" в меню ниже. '
                                       f'При отсутствии меню нажмите кнопку с 4-мя кружками',
                                  reply_markup=kb.keyboard_report_start())
    await state.set_state(state=None)
    await callback.answer()


@router.message(F.text == 'Завершить отчет')
async def process_get_complete_part(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Запускаем процесс завершение отчета
    :param message:
    :param state:
    :return:
    """
    logging.info(f"process_get_complete_pert {message.chat.id}")
    await message.answer('Завершить отчет',
                         reply_markup=kb.keyboard_again_finish())
    # await bot.delete_message(chat_id=message.chat.id,
    #                          message_id=message.message_id-1)
    reports = await rq.get_reports_creator_status(creator=message.chat.id, status=rq.ReportStatus.create)
    list_report = [report for report in reports]
    if not list_report:
        await message.answer(text='У вас нет открытых отчетов. чтобы открыть отчет нажмите "Создать отчет"')
        return
    await message.answer(text='Выберите отчет для его завершения',
                         reply_markup=kb.keyboard_select_report_complete(list_report=list_report,
                                                                         callback_report='comletereport'))
#     await message.answer(text=f'Пришлите QR-код для завершения отчета . Для добавления QR нажмите на 📎',
#                          reply_markup=kb.keyboard_again_finish())
#     await state.set_state(Report.QR_2)
#
#
# @router.message(F.photo, StateFilter(Report.QR_2))
# async def process_get_qr(message: Message, state: FSMContext) -> None:
#     """
#     Получаем QR от пользователя
#     :param message:
#     :param state:
#     :return:
#     """
#     logging.info(f"process_start_command {message.chat.id}")
#     qr_id = message.photo[-1].file_id
#     file_path = f"data/{qr_id}.jpg"
#     await message.bot.download(
#         qr_id,
#         destination=file_path
#     )
#     img_qrcode = cv2.imread(file_path)
#     detector = cv2.QRCodeDetector()
#     data, bbox, clear_qrcode = detector.detectAndDecode(img_qrcode)
#     if data:
#         list_qr = []
#         for _ in data.split("\n"):
#             list_qr.append(_.split(":")[1])
#         await state.update_data(report_id=' ')
#         report = await rq.get_report_number(number=list_qr[0])
#         if not report:
#             await message.answer(text=f"Открытый отчет с номер заказа {list_qr[0]} не найден."
#                                       f" Создайте отчет с этим номера заказа или введите номер отчета вручную",
#                                  reply_markup=kb.keyboard_not_report())
#             return
#         list_reports = [report.part_title for report in (await rq.get_reports_number(number=list_qr[0]))]
#         print(list_reports)
#         # elif report.status == rq.ReportStatus.complied:
#         #     await message.answer(text=f"Отчет с номер заказа {list_qr[0]} уже завершен.",
#         #                          reply_markup=kb.keyboard_not_report())
#         #     return
#         await state.update_data(report_id=report.id)
#         try:
#             os.remove(file_path)
#             logging.info(f'Файл {file_path} успешно удалён.')
#         except FileNotFoundError:
#             logging.error(f'Файл {file_path} не найден.')
#         except PermissionError:
#             logging.error(f'У вас нет разрешения на удаление файла {file_path}.')
#         except Exception as e:
#             logging.error(f'Произошла ошибка: {e}')
#
#     else:
#         await message.answer(text='QR не распознан',
#                              reply_markup=kb.keyboard_not_recognize_finish())
#         try:
#             os.remove(file_path)
#             logging.info(f'Файл {file_path} успешно удалён.')
#         except FileNotFoundError:
#             logging.error(f'Файл {file_path} не найден.')
#         except PermissionError:
#             logging.error(f'У вас нет разрешения на удаление файла {file_path}.')
#         except Exception as e:
#             logging.error(f'Произошла ошибка: {e}')
#         return


@router.callback_query(F.data.startswith('comletereport'))
async def process_select_report(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора отчета для заверения и вывод списка названий операций
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"process_select_report {callback.message.chat.id}")
    report_id = int(callback.data.split('_')[-1])
    # list_title_action = await get_list_all_rows(data='action')
    await state.update_data(report_id=report_id)
    data_complete = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
    await rq.set_report(report_id=report_id,
                        data={"data_complete": data_complete})

    time.sleep(0.1)
    # text_user = await user_text(tg_id=callback.message.chat.id)
    # text_report = await report_text(report_id=report_id,
    #                                 report_data=['number_order',
    #                                              'part_designation',
    #                                              'part_title',
    #                                              'title_machine',
    #                                              'data_create',
    #                                              'data_complete'])
    # await callback.message.edit_text(text=f'{text_user}{text_report}'
    #                                       f'Выберите название операции:',
    #                                  reply_markup=kb.keyboard_select_report(list_report=list_title_action,
    #                                                                         callback_report='action'))


# @router.callback_query(F.data == 'open_report')
# async def process_open_report(callback: CallbackQuery, state: FSMContext, bot: Bot):
#     logging.info(f"process_open_report {callback.message.chat.id}")
#     text_user = await user_text(tg_id=callback.message.chat.id)
#     await bot.delete_message(chat_id=callback.message.chat.id,
#                              message_id=callback.message.message_id)
#     await callback.message.answer(text=f'{text_user}'
#                                        f'Для начала отчета отправьте фотографию.'
#                                        f' Для добавления фотографии нажмите на 📎',
#                                   reply_markup=kb.keyboard_again_start())
#     await state.set_state(Report.photo)


# @router.callback_query(F.data == 'input_number_report')
# async def process_input_number_report(callback: CallbackQuery, state: FSMContext, bot: Bot):
#     logging.info(f"process_input_number_report {callback.message.chat.id}")
#     await callback.message.edit_text(text='Введите номер заказа',
#                                      reply_markup=None)
#     await state.set_state(Report.find_number_order)
#     await callback.answer()


# @router.callback_query(F.data == 'qr_recognize_finish')
# async def process_qr_recognize_finish(callback: CallbackQuery, state: FSMContext, bot: Bot):
#     logging.info(f"process_qr_recognize_finish {callback.message.chat.id}")
#     await callback.message.answer(text=f'Пришлите фото QR-кода. Для добавления QR нажмите на 📎',
#                                   reply_markup=kb.keyboard_report_start())
#     await state.set_state(Report.QR_2)


# @router.message(F.text, StateFilter(Report.find_number_order))
# async def get_input_number_report(message: Message, state: FSMContext):
#     logging.info(f"get_input_number_report {message.chat.id}")
#     report = await rq.get_report_number(number=message.text)
#     if not report:
#         await message.answer(text=f"Открытый отчет с номер заказа {message.text} не найден."
#                                   f" Создайте отчет с этим номера заказа или введите номер отчета вручную",
#                              reply_markup=kb.keyboard_not_report())
#         return
#     list_reports = [report.part_designation for report in (await rq.get_reports_number(number=message.text))]
#     await message.answer(text="Выберите отчет для его завершения",
#                          reply_markup=kb.keyboard_select_report(list_report=list_reports, callback_report='report'))
#     await state.set_state(state=None)

#
# @router.callback_query(F.data.startswith('report'))
# async def process_select_report(callback: CallbackQuery, state: FSMContext):
#     """
#     Выбор отчета для его завершения
#     :param callback:
#     :param state:
#     :return:
#     """
#     logging.info(f"process_select_report")
#     designation_part = callback.data.split('_')[-1]
#     report = await rq.get_report_designation_part(designation_part=designation_part)
#
#     list_title_action = await get_list_all_rows(data='action')
#     report_id = report.id
#     await state.update_data(report_id=report_id)
#     data_complete = datetime.today().strftime('%H/%M/%S/%d/%m/%Y')
#     await rq.set_report(report_id=report_id,
#                         data={"data_complete": data_complete})
#
#     time.sleep(0.1)
#     text_user = await user_text(tg_id=callback.message.chat.id)
#     text_report = await report_text(report_id=report_id,
#                                     report_data=['number_order',
#                                                  'part_designation',
#                                                  'part_title',
#                                                  'data_create',
#                                                  'data_complete'])
#     await callback.message.edit_text(text=f'{text_user}{text_report}'
#                                           f'Выберите название операции:',
#                                      reply_markup=kb.keyboard_select_report(list_report=list_title_action,
#                                                                             callback_report='action'))
#     await callback.answer()


# @router.callback_query(F.data.startswith('action'))
# async def process_select_title_action(callback: CallbackQuery, state: FSMContext):
#     """
#     Выбрать наименование операции
#     :param callback:
#     :param state:
#     :return:
#     """
#     logging.info(f'process_select_title_action {callback.message.chat.id}')
#     list_operation = await get_list_all_rows(data='operation')
#     data = await state.get_data()
#     report_id = data['report_id']
#     await rq.set_report(report_id=report_id,
#                         data={"title_action": callback.data.split('_')[1]})
#     time.sleep(0.1)
    list_operation = await get_list_all_rows(data='operation')
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'title_machine',
                                                 'data_create',
                                                 'data_complete'])
    # await callback.message.edit_text(text=f'{text_user}{text_report}'
    #                                       f'Выберите описание операции:',
    #                                  reply_markup=kb.keyboard_select_report(list_report=list_operation,
    #                                                                         callback_report='operation'))
    await callback.message.edit_text(text=f'{text_user}{text_report}'
                                          f'Выберите описание операции:',
                                     reply_markup=kb.keyboard_operation())

    await callback.answer()


@router.callback_query(F.data.startswith('operation'))
async def process_select_description_operation(callback: CallbackQuery, state: FSMContext):
    """
    Выбор описания операции
    :param callback:
    :param state:
    :return:
    """
    logging.info(f"process_select_description_operation {callback.message.chat.id}")
    # list_title_machine = await get_list_all_rows(data='title_machine')
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"description_action": callback.data.split('_')[1]})
    #
    # time.sleep(0.1)
    # text_user = await user_text(tg_id=callback.message.chat.id)
    # text_report = await report_text(report_id=report_id,
    #                                 report_data=['number_order',
    #                                              'part_designation',
    #                                              'title_action',
    #                                              'part_title',
    #                                              'description_action',
    #                                              'title_machine',
    #                                              'data_create',
    #                                              'data_complete'])
    # await callback.message.edit_text(text=f'{text_user}{text_report}'
    #                                       f'Выберите наименование станка:',
    #                                  reply_markup=kb.keyboard_select_report(list_report=list_title_machine,
    #                                                                         callback_report='tmachine'))
    # await callback.answer()
#
#
# @router.callback_query(F.data.startswith('tmachine'))
# async def process_select_description_operation(callback: CallbackQuery, state: FSMContext):
#     """
#     Выбор описания операции
#     :param callback:
#     :param state:
#     :return:
#     """
#     text_user = await user_text(tg_id=callback.message.chat.id)
#     data = await state.get_data()
#     report_id = data['report_id']
#     await rq.set_report(report_id=report_id,
#                         data={"title_machine": callback.data.split('_')[1]})
#     report_info = await rq.get_report(report_id=report_id)
#     date_format = '%H/%M/%S/%d/%m/%Y'
#     machine_time = datetime.strptime(report_info.data_complete,
#                                      date_format) - datetime.strptime(report_info.data_create, date_format)
#     await rq.set_report(report_id=report_id,
#                         data={"machine_time": machine_time.seconds})
#
#     time.sleep(0.1)
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'data_create',
                                                 'data_complete'])
    await callback.message.edit_text(text=f'{text_user}{text_report}'
                                          f'Введите количество деталей, прошедших операцию')
    await callback.answer()
    await state.set_state(Report.count_part)


@router.message(F.text, StateFilter(Report.count_part))
async def process_get_count_part(message: Message, state: FSMContext) -> None:
    """
    Получение количества изготовленных деталей
    :param message:
    :param state:
    :return:
    """
    logging.info(f'process_get_count_part {message.chat.id}')
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer(text='Количество деталей должно быть целым числом, указанным цифрами')
        return
    # !!! Здесь считаем среднее время

    data = await state.get_data()
    report_id = data['report_id']
    report_info = await rq.get_report(report_id=report_id)
    date_format = '%H:%M:%S %d-%m-%Y'
    average_time = (datetime.strptime(report_info.data_complete,
                                     date_format) - datetime.strptime(report_info.data_create,
                                                                      date_format))

    await rq.set_report(report_id=report_id,
                        data={"average_time": round(average_time.seconds/60/int(message.text), 2)})

    time.sleep(0.1)
    await rq.set_report(report_id=report_id,
                        data={"count_part": message.text})
    await state.set_state(state=None)
    time.sleep(0.1)
    text_user = await user_text(tg_id=message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'data_create',
                                                 'data_complete'])
    await message.answer(text=f'{text_user}{text_report}'
                              f'Все ли детали из партии прошли операцию',
                         reply_markup=kb.keyboard_is_all_installed())


@router.callback_query(F.data.startswith('is_all_installed'))
async def is_all_installed(callback: CallbackQuery, state: FSMContext):
    """
    Все ли детали установлены
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'is_all_installed {callback.message.chat.id}')
    answer = callback.data.split('_')[-1]
    data = await state.get_data()
    report_id = data['report_id']
    if answer == 'yes':
        await rq.set_report(report_id=report_id,
                            data={"is_all_installed": 'Да'})
    else:
        await rq.set_report(report_id=report_id,
                            data={"is_all_installed": 'Нет'})
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'data_create',
                                                 'data_complete'])
    await callback.message.edit_text(text=f'{text_user}{text_report}'
                                          f'Есть ли брак?',
                                     reply_markup=kb.keyboard_is_defect())
    await callback.answer()


@router.callback_query(F.data.startswith('is_defect'))
async def is_defect(callback: CallbackQuery, state: FSMContext):
    """
    Все ли детали установлены
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'is_defect {callback.message.chat.id}')
    answer = callback.data.split('_')[-1]
    data = await state.get_data()
    report_id = data['report_id']
    if answer == 'yes':
        await rq.set_report(report_id=report_id,
                            data={"is_defect": 'Да'})
    else:
        # await callback.answer(text='⚠️Информационное сообщение⚠️\n\n'
        #                            'Если нет брака пропускаем пункты с их количеством и причиной,'
        #                            ' их можно изменить позже при проверке отчета', show_alert=True)
        await rq.set_report(report_id=report_id,
                            data={"is_defect": 'Нет'})
        await rq.set_report(report_id=report_id,
                            data={"count_defect": "0"})
        await rq.set_report(report_id=report_id,
                            data={"reason_defect": "none"})
        text_user = await user_text(tg_id=callback.message.chat.id)
        text_report = await report_text(report_id=report_id,
                                        report_data=['number_order',
                                                     'part_designation',
                                                     'number_MSK',
                                                     'title_action',
                                                     'part_title',
                                                     'description_action',
                                                     'title_machine',
                                                     'average_time',
                                                     'count_part',
                                                     'is_all_installed',
                                                     'is_defect',
                                                     'data_create',
                                                     'data_complete'])
        await callback.message.edit_text(text=f'{text_user}{text_report}'
                                              f'Работа на 1 или 2-х станках?',
                                         reply_markup=kb.keyboard_count_machine())
        await callback.answer()
        return
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'data_create',
                                                 'data_complete'])
    await callback.message.edit_text(text=f'{text_user}{text_report}'
                                          f'Количество брака?')
    await state.set_state(Report.count_defect)
    await callback.answer()


@router.message(StateFilter(Report.count_defect))
async def get_count_defect(message: Message, state: FSMContext):
    """
    Получить количество деталей с дефектами
    :param message:
    :param state:
    :return:
    """
    logging.info(f'get_count_defect {message.chat.id}')
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer(text='Количество деталей должно быть целым числом, указанным цифрами')
        return
    data = await state.get_data()
    report_id = data['report_id']
    info_report = await rq.get_report(report_id=report_id)
    if int(info_report.count_part) < int(message.text):
        await message.answer(text='Количество деталей брака не может превышать количество изготовленных деталей.'
                                  ' Повторите ввод')
        return
    await rq.set_report(report_id=report_id,
                        data={"count_defect": message.text})
    text_user = await user_text(tg_id=message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'data_create',
                                                 'data_complete'])
    if int(message.text) > 0:
        await message.answer(text=f'{text_user}{text_report}'
                                  f'Причина брака?')
        await state.set_state(Report.reason_defect)
    else:
        await message.answer(text=f'{text_user}{text_report}'
                                  f'Работа на 1 или 2-х станках?',
                             reply_markup=kb.keyboard_count_machine())


@router.message(StateFilter(Report.reason_defect))
async def get_reason_defect(message: Message, state: FSMContext):
    """
    Получить причину дефекта
    :param message:
    :param state:
    :return:
    """
    logging.info(f'get_reason_defect {message.chat.id}')
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"reason_defect": message.text})
    text_user = await user_text(tg_id=message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'reason_defect',
                                                 'data_create',
                                                 'data_complete'])
    await message.answer(text=f'{text_user}{text_report}'
                              f'Работа на 1 или 2-х станках?',
                         reply_markup=kb.keyboard_count_machine())
    await state.set_state(state=None)


@router.callback_query(F.data.startswith('count_machine'))
async def count_machine(callback: CallbackQuery, state: FSMContext):
    """
    Количество станков
    :param callback:
    :param state:
    :return:
    """
    logging.info(f'count_machine {callback.message.chat.id}')
    answer = callback.data.split('_')[-1]
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"count_machine": answer})
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'reason_defect',
                                                 'count_machine',
                                                 'data_create',
                                                 'data_complete'])
    await callback.message.edit_text(text=f'{text_user}{text_report}'
                                          f'Укажите машинное время в минутах')
    await state.set_state(Report.machine_time)
    await callback.answer()


@router.message(StateFilter(Report.machine_time))
async def get_time_machine(message: Message, state: FSMContext):
    """
    Получаем машинное время и просим добавить примечание
    :param message:
    :param state:
    :return:
    """
    logging.info(f'get_time_machine {message.chat.id}')
    re_int = re.compile(r"(^[1-9]+\d*$|^0$)")
    re_float = re.compile(r"(^\d+\.\d+$|^\.\d+$)")
    if not message.text.isdigit():
        if not re_int.match(message.text) and not re_float.match(message.text):
            await message.answer(text='Время должно быть числом')
            return
    time_machine = message.text
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"machine_time": time_machine})
    text_user = await user_text(tg_id=message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'reason_defect',
                                                 'count_machine',
                                                 'machine_time',
                                                 'data_create',
                                                 'data_complete'])

    await message.answer(text=f'{text_user}{text_report}'
                              f'Добавьте примечание',
                         reply_markup=kb.keyboard_skip())
    await state.set_state(Report.note_report)


# @router.callback_query(F.data == 'skip')
# async def skip_note_report(callback: CallbackQuery, state: FSMContext):
#     """
#     Пропуск добавления примечания
#     :param callback:
#     :param state:
#     :return:
#     """
#     logging.info(f"skip_note_report {callback.message.chat.id}")
#     data = await state.get_data()
#     report_id = data['report_id']
#     await rq.set_report(report_id=report_id,
#                         data={"note_report": 'None'})
#     await state.set_state(state=None)
#     text_user = await user_text(tg_id=callback.message.chat.id)
#     text_report = await report_text(report_id=report_id,
#                                     report_data=['number_order',
#                                                  'part_designation',
#                                                  'title_action',
#                                                  'part_title',
#                                                  'description_action',
#                                                  'title_machine',
#                                                  'average_time',
#                                                  'count_part',
#                                                  'is_all_installed',
#                                                  'is_defect',
#                                                  'count_defect',
#                                                  'reason_defect',
#                                                  'note_report',
#                                                  'data_create',
#                                                  'data_complete'])
#     await callback.message.answer(text=f'Отчет заполнен\n\n'
#                                        f'{text_user}{text_report}\n\n'
#                                        f'Проверьте и измените если необходимо',
#                                   reply_markup=kb.keyboard_check_report())
#     await callback.answer()


# @router.message(StateFilter(Report.note_report))
# async def get_note_report(message: Message, state: FSMContext):
#     """
#     Получить примечание
#     :param message:
#     :param state:
#     :return:
#     """
#     logging.info(f'get_note_report {message.chat.id}')
#     data = await state.get_data()
#     report_id = data['report_id']
#     await rq.set_report(report_id=report_id,
#                         data={"note_report": message.text})
#     await state.set_state(state=None)
#     text_user = await user_text(tg_id=message.chat.id)
#     text_report = await report_text(report_id=report_id,
#                                     report_data=['number_order',
#                                                  'part_designation',
#                                                  'title_action',
#                                                  'part_title',
#                                                  'description_action',
#                                                  'title_machine',
#                                                  'average_time',
#                                                  'count_part',
#                                                  'is_all_installed',
#                                                  'is_defect',
#                                                  'count_defect',
#                                                  'reason_defect',
#                                                  'note_report',
#                                                  'data_create',
#                                                  'data_complete'])
#     await message.answer(text=f'Отчет заполнен\n\n'
#                               f'{text_user}{text_report}\n\n'
#                               f'Проверьте и измените если необходимо',
#                          reply_markup=kb.keyboard_check_report())


@router.message(StateFilter(Report.note_report))
async def get_note_report(message: Message, state: FSMContext, bot: Bot):
    """
    Получить примечание
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_note_report {message.chat.id}')
    await message.answer(text='Проверка отчета',
                         reply_markup=kb.keyboard_confirm_report())
    data = await state.get_data()
    report_id = data['report_id']
    await rq.set_report(report_id=report_id,
                        data={"note_report": message.text})
    await state.set_state(state=None)
    data = await state.get_data()
    report_id = data['report_id']
    report_info = await rq.get_report(report_id=report_id)
    text_user = await user_text(tg_id=message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'reason_defect',
                                                 'note_report',
                                                 'machine_time',
                                                 'data_create',
                                                 'data_complete'])
    check_message = await message.answer_photo(photo=report_info.photo_id,
                                               caption=f'{text_user}{text_report}',
                                               reply_markup=kb.keyboard_change_report(info_report=report_info))
    await state.set_state(state=None)
    await state.update_data(check_message=check_message.message_id)


@router.callback_query(F.data == 'skip')
async def check_report(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Проверить отчет
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'check_report {callback.message.chat.id}')
    await callback.message.answer(text='Проверка отчета',
                                  reply_markup=kb.keyboard_confirm_report())
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    data = await state.get_data()
    report_id = data['report_id']
    report_info = await rq.get_report(report_id=report_id)
    text_user = await user_text(tg_id=callback.message.chat.id)
    text_report = await report_text(report_id=report_id,
                                    report_data=['number_order',
                                                 'part_designation',
                                                 'number_MSK',
                                                 'title_action',
                                                 'part_title',
                                                 'description_action',
                                                 'title_machine',
                                                 'average_time',
                                                 'count_part',
                                                 'is_all_installed',
                                                 'is_defect',
                                                 'count_defect',
                                                 'reason_defect',
                                                 'note_report',
                                                 'machine_time',
                                                 'data_create',
                                                 'data_complete'])
    check_message = await callback.message.answer_photo(photo=report_info.photo_id,
                                                        caption=f'{text_user}{text_report}',
                                                        reply_markup=kb.keyboard_change_report(info_report=report_info))
    await state.update_data(check_message=check_message.message_id)
    await state.set_state(state=None)
    await callback.answer()
