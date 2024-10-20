import gspread
import logging
# TEST

gp = gspread.service_account(filename='services/nevis.json')
bot_data = gp.open('bot_данные')
bot_report = gp.open('bot_отчеты')
reports = bot_report.worksheet("Лист1")
units = bot_data.worksheet("подразделения")
users = bot_data.worksheet("пользователи")
machines = bot_data.worksheet("оборудование")


async def append_report(data: list) -> None:
    """
    Добавление отчета в гугл таблицу
    :param data:
    :return:
    """
    logging.info(f'append_report')
    reports.append_row(data)


async def append_user(data: list) -> None:
    """
    Добавление пользователя в гугл таблицу
    :param data: ID	ФИО	Должность Участок data=[user_info.tg_id, user_info.fullname, user_info.job, user_info.district]
    :return:
    """
    logging.info(f'append_user')
    values = users.get_all_values()
    for i, item in enumerate(values[1:]):
        if item[0] == str(data[0]):
            users.update_cell(i + 2, 2, data[1])
            users.update_cell(i + 2, 3, data[2])
            users.update_cell(i + 2, 4, data[3])
            break
    else:
        users.append_row(data)


async def get_list_all_rows(data: str, tittle_action: str = None) -> list:
    logging.info(f'get_list_all_rows')
    list_product = []
    if data == 'job':
        values = units.get_all_values()
        for item in values[1:]:
            list_product.append(item[1])
    elif data == 'district':
        values = units.get_all_values()
        for item in values[1:]:
            list_product.append(item[0])
    elif data == 'action':
        values = machines.get_all_values()
        for item in values[1:]:
            list_product.append(item[0])
    elif data == 'title_machine':
        values = machines.get_all_values()
        for item in values[1:]:
            if item[0] == tittle_action:
                list_product.append(item[1])

    return list(set(list_product))
