from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Report
import logging

keyboard_report_text_button = {}


def keyboard_operation() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора описания операции
    """
    logging.info("keyboard_operation")
    button_1 = InlineKeyboardButton(text='Наладка оборудования', callback_data=f'change_operation_Наладка оборудования')
    button_2 = InlineKeyboardButton(text='Обработка заготовки', callback_data=f'change_operation_Обработка заготовки')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]],)
    return keyboard


def keyboard_report_start() -> ReplyKeyboardMarkup:
    logging.info("keyboard_report_start")
    button_1 = KeyboardButton(text=f'Мой профиль')
    button_2 = KeyboardButton(text=f'Создать отчет')
    button_3 = KeyboardButton(text=f'Завершить отчет')
    # button_4 = KeyboardButton(text='🔄 Заполнить отчет заново')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2], [button_3]],
                                   resize_keyboard=True)
    return keyboard
#
#
# def keyboard_report_start() -> ReplyKeyboardMarkup:
#     logging.info("keyboard_report_start")
#     button_1 = KeyboardButton(text=f'Мой профиль')
#     button_2 = KeyboardButton(text=f'Создать отчет')
#     button_3 = KeyboardButton(text=f'Завершить отчет')
#     button_4 = KeyboardButton(text='🔄 Заполнить отчет заново')
#     keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2], [button_3], [button_4]],
#                                    resize_keyboard=True)
#     return keyboard
#
#
# def keyboard_report_start_2() -> ReplyKeyboardMarkup:
#     logging.info("keyboard_report_start")
#     button_1 = KeyboardButton(text=f'Мой профиль')
#     button_2 = KeyboardButton(text=f'Создать отчет')
#     button_3 = KeyboardButton(text=f'Завершить отчет')
#     button_4 = KeyboardButton(text='Заполнить отчет заново 🔄')
#     keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2], [button_3], [button_4]],
#                                    resize_keyboard=True)
#     return keyboard
#
#
# def keyboard_again() -> ReplyKeyboardMarkup:
#     logging.info("keyboard_again")
#     button_1 = KeyboardButton(text='Заполнить отчет заново 🔄',)
#     keyboard = ReplyKeyboardMarkup(keyboard=[[button_1]],
#                                    resize_keyboard=True)
#     return keyboard


def keyboard_action(list_title_action: list) -> InlineKeyboardMarkup:
    logging.info(f"keyboard_action")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for action in list_title_action:
        text = action
        button = f'action_{action}'
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=button))
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()


def keyboard_select_report(list_report: list, callback_report: str) -> InlineKeyboardMarkup:
    logging.info(f"keyboard_select_report")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for action in list_report:
        text = action
        button = f'{callback_report}_{action}'
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=button))
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()


def keyboard_is_all_installed() -> InlineKeyboardMarkup:
    logging.info("keyboard_is_all_installed")
    button_1 = InlineKeyboardButton(text='Да', callback_data=f'is_all_installed_yes')
    button_2 = InlineKeyboardButton(text='Нет', callback_data=f'is_all_installed_no')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]],)
    return keyboard


def keyboard_is_defect() -> InlineKeyboardMarkup:
    logging.info("keyboard_is_defect")
    button_1 = InlineKeyboardButton(text='Да', callback_data=f'is_defect_yes')
    button_2 = InlineKeyboardButton(text='Нет', callback_data=f'is_defect_no')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]],)
    return keyboard


def keyboard_count_machine() -> InlineKeyboardMarkup:
    logging.info("keyboard_count_machine")
    button_1 = InlineKeyboardButton(text='1 станок', callback_data=f'count_machine_1')
    button_2 = InlineKeyboardButton(text='2 станок', callback_data=f'count_machine_2')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]],)
    return keyboard


def keyboard_check_report() -> InlineKeyboardMarkup:
    logging.info("keyboard_check_report")
    button_1 = InlineKeyboardButton(text='Проверить отчет', callback_data=f'check_report')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]],)
    return keyboard


def keyboard_change_report(info_report: Report) -> InlineKeyboardMarkup:
    logging.info("keyboard_change_report")
    button_1 = InlineKeyboardButton(text=f'№ заказ: {info_report.number_order}',
                                    callback_data=f'change_report-number_order')
    button_2 = InlineKeyboardButton(text=f'Обозначение детали: {info_report.part_designation}',
                                    callback_data=f'change_report-part_designation')
    button_3 = InlineKeyboardButton(text=f'Наименование детали: {info_report.part_title}',
                                    callback_data=f'change_report-part_title')
    button_4 = InlineKeyboardButton(text=f'Название операции: {info_report.title_action}',
                                    callback_data=f'change_report-title_action')
    button_5 = InlineKeyboardButton(text=f'Описание операции: {info_report.description_action}',
                                    callback_data=f'change_report_description_action')

    button_6 = InlineKeyboardButton(text=f'Наименование станка: {info_report.title_machine}',
                                    callback_data=f'change_report-title_machine')
    button_7 = InlineKeyboardButton(text=f'Количество деталей: {info_report.count_part}',
                                    callback_data=f'change_report-count_part')
    button_8 = InlineKeyboardButton(text=f'Все ли детали установлены: {info_report.is_all_installed}',
                                    callback_data=f'change_report-is_all_installed')
    button_9 = InlineKeyboardButton(text=f'Есть ли брак: {info_report.is_defect}',
                                    callback_data=f'change_report-is_defect')

    button_10 = InlineKeyboardButton(text=f'Кол-во брака: {info_report.count_defect}',
                                     callback_data=f'change_report-count_defect')
    button_11 = InlineKeyboardButton(text=f'Причина брака: {info_report.reason_defect if info_report.reason_defect != "none" else "Отсутствует"}',
                                     callback_data=f'change_report-reason_defect')
    button_12 = InlineKeyboardButton(text=f'Работа на 1 или 2-х станках?: {info_report.count_machine}',
                                     callback_data=f'change_report-count_machine')
    button_13 = InlineKeyboardButton(text=f'Машинное время: {info_report.machine_time}',
                                     callback_data=f'change_report-machine_time')
    button_14 = InlineKeyboardButton(text=f'Начало работы: {info_report.data_create}',
                                     callback_data=f'change_report-data_create')
    button_15 = InlineKeyboardButton(text=f'Окончание работы: {info_report.data_complete}',
                                     callback_data=f'change_report-reason_defect')
    button_16 = InlineKeyboardButton(text=f'Комментарий: {info_report.note_report}',
                                     callback_data=f'change_report-note_report')
    if info_report.is_defect == 'Да':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_5],
                                                         [button_7], [button_8], [button_9],
                                                         [button_10], [button_11], [button_12], [button_13], [button_16]],)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_5],
                                                         [button_7], [button_8], [button_9],
                                                         [button_12], [button_13], [button_16]],)
    return keyboard
