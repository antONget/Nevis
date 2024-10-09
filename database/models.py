from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from dataclasses import dataclass


engine = create_async_engine(url="sqlite+aiosqlite:///database/db.sqlite3", echo=False)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String(20))
    fullname: Mapped[str] = mapped_column(String(20), default='default')
    job: Mapped[str] = mapped_column(String(20), default='default')
    district: Mapped[str] = mapped_column(String(20), default='default')


class Report(Base):
    __tablename__ = 'reports'

    id: Mapped[int] = mapped_column(primary_key=True)
    creator = mapped_column(Integer)
    photo_id: Mapped[str] = mapped_column(String(200))
    number_order: Mapped[str] = mapped_column(String(20))
    part_designation: Mapped[str] = mapped_column(String(200))
    number_MSK: Mapped[str] = mapped_column(String(200))
    part_title: Mapped[str] = mapped_column(String(200))
    data_create: Mapped[str] = mapped_column(String(200))
    title_action: Mapped[str] = mapped_column(String(200), default='none')
    description_action: Mapped[str] = mapped_column(String(200), default='none')
    title_machine: Mapped[str] = mapped_column(String(200), default='none')
    machine_time: Mapped[str] = mapped_column(String(200), default='none')
    average_time: Mapped[str] = mapped_column(String(200), default='none')
    count_part: Mapped[str] = mapped_column(String(200), default='none')
    is_all_installed: Mapped[str] = mapped_column(String(200), default='none')
    is_defect: Mapped[str] = mapped_column(String(200), default='none')
    count_defect: Mapped[str] = mapped_column(String(200), default='none')
    reason_defect: Mapped[str] = mapped_column(String(200), default='none')
    count_machine: Mapped[str] = mapped_column(String(200), default='none')
    data_complete: Mapped[str] = mapped_column(String(200), default='none')
    note_report:  Mapped[str] = mapped_column(String(200), default='none')
    status: Mapped[str] = mapped_column(String(200), default='start')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# import asyncio
#
# asyncio.run(async_main())
