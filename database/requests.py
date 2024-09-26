from database.models import User, Report
from database.models import async_session
from sqlalchemy import select, update, delete
from dataclasses import dataclass
import logging


"""USER"""


async def add_user(tg_id: int, data: dict) -> None:
    """
    Добавляем нового пользователя если его еще нет в БД
    :param tg_id:
    :param data:
    :return:
    """
    logging.info(f'add_user')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        # если пользователя нет в базе
        if not user:
            session.add(User(**data))
            await session.commit()


async def set_fullname(fullname: str, tg_id: int) -> None:
    """
    Обновляем ФИО пользователя
    :param fullname:
    :param tg_id:
    :return:
    """
    logging.info(f'set_fullname')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.fullname = fullname
            await session.commit()


async def set_job(job: str, tg_id: int) -> None:
    """
    Обновляем должность пользователя
    :param job:
    :param tg_id:
    :return:
    """
    logging.info(f'set_job')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.job = job
            await session.commit()


# async def set_power(power: str, tg_id: int) -> None:
#     """
#     Обновляем значение мощности
#     :param power:
#     :param tg_id:
#     :return:
#     """
#     logging.info(f'set_power')
#     async with async_session() as session:
#         user = await session.scalar(select(User).where(User.tg_id == tg_id))
#         if user:
#             user.power = power
#             await session.commit()


async def set_district(district: str, tg_id: int) -> None:
    """
    Обновляем значение участка
    :param district:
    :param tg_id:
    :return:
    """
    logging.info(f'set_district')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.district = district
            await session.commit()


async def get_user_tg_id(tg_id: int) -> User:
    """
    Получаем информацию по пользователю
    :param tg_id:
    :return:
    """
    logging.info(f'get_user_tg_id')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user


async def get_all_users() -> list[User]:
    """
    Получаем список всех пользователей зарегистрированных в боте
    :return:
    """
    logging.info(f'get_all_users')
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users


async def check_registration(tg_id: int) -> bool:
    """
    Проверка на то что все поля заполнены
    :return:
    """
    logging.info(f'check_registration')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id,
                                                       User.job != 'default',
                                                       User.district != 'default',
                                                       User.fullname != 'default'))
        if user:
            return True
        else:
            return False


@dataclass
class ReportStatus:
    start = "start"
    create = "create"
    process = "process"
    complied = "complied"


""" REPORT """


async def add_report(data: dict) -> None:
    """
    Добавляем отчет
    :param data:
    :return:
    """
    logging.info(f'add_report')
    async with async_session() as session:
        report = Report(**data)
        session.add(report)
        await session.flush()
        report_id = report.id
        await session.commit()
        return report_id


async def get_report(report_id: int) -> Report:
    """
    Получаем отчет по его id
    :param report_id:
    :return:
    """
    logging.info(f'add_report')
    async with async_session() as session:
        return await session.scalar(select(Report).where(Report.id == report_id))


async def get_report_number(number: str) -> Report:
    """
    Получаем отчет по его id
    :param number:
    :return:
    """
    logging.info(f'add_report')
    async with async_session() as session:
        return await session.scalar(select(Report).where(Report.number_order == number))


async def set_report(report_id: int, data: dict) -> None:
    """
    Обновляем отчет по его id
    :param report_id:
    :param data:
    :return:
    """
    logging.info(f'set_report')
    async with async_session() as session:
        report = await session.scalar(select(Report).where(Report.id == report_id))
        if 'title_action' in data.keys():
            report.title_action = data['title_action']
        elif 'description_action' in data.keys():
            report.description_action = data['description_action']
        elif 'title_machine' in data.keys():
            report.title_machine = data['title_machine']
        elif 'machine_time' in data.keys():
            report.machine_time = data['machine_time']
        elif 'data_complete' in data.keys():
            report.data_complete = data['data_complete']
        elif 'count_part' in data.keys():
            report.count_part = data['count_part']
        elif 'is_all_installed' in data.keys():
            report.is_all_installed = data['is_all_installed']
        elif 'is_defect' in data.keys():
            report.is_defect = data['is_defect']
        elif 'count_defect' in data.keys():
            report.count_defect = data['count_defect']
        elif 'reason_defect' in data.keys():
            report.reason_defect = data['reason_defect']
        elif 'count_machine' in data.keys():
            report.count_machine = data['count_machine']
        elif 'note_report' in data.keys():
            report.note_report = data['note_report']
        elif 'number_order' in data.keys():
            report.number_order = data['number_order']
        elif 'description_action' in data.keys():
            report.description_action = data['description_action']
        elif 'part_title' in data.keys():
            report.part_title = data['part_title']
        elif 'data_create' in data.keys():
            report.data_create = data['data_create']
        elif 'data_complete' in data.keys():
            report.data_complete = data['data_complete']
        elif 'part_designation' in data.keys():
            report.part_designation = data['part_designation']
        elif 'status' in data.keys():
            report.status = data['status']
        await session.commit()
