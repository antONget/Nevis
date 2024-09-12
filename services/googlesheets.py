import gspread
import logging
# TEST

gp = gspread.service_account(filename='services/kingdom.json')
gsheet = gp.open('Исходные данные')
job = gsheet.worksheet("Должность")
power = gsheet.worksheet("Мощность")
district = gsheet.worksheet("Участок")
report = gsheet.worksheet("Отчет")


async def append_row(data: list) -> None:
    logging.info(f'append_row')
    report.append_row(data)


async def get_list_all_rows(data: str) -> list:
    logging.info(f'get_list_all_rows')
    if data == 'job':
        sheet = job
    elif data == 'power':
        sheet = power
    elif data == 'district':
        sheet = district
    values = sheet.get_all_values()
    list_product = []
    for item in values[1:]:
        list_product.append(item[1])
    return list_product
