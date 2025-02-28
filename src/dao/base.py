import logging
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Sequence, delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.config import Base

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession) -> T:
        """Searching only one database_url model by it's id.

        Args:
            data_id: id to search by.
            session: Database session object.

        Returns:
            A database_url object if found by it's id.
        """
        logger.debug(f"Поиск {cls.model.__name__} c ID: {data_id}")
        try:
            return await session.get(cls.model, data_id)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске {cls.model.__name__} c ID: {data_id}: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel) -> Sequence[T]:
        """
        Searching only one database_url model by pydantic base model.
        Args:
            session: Database async session object.
            filters: Provided pydantic base model.

        Returns:
            A database_url object if found.
        """
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.debug(f"Поиск ОДНОЙ записи {cls.model.__name__} по фильтрам {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи по фильтрам {filter_dict}: {e}")
            raise e

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None) -> Sequence[T]:
        """
        Searching many models by pydantic model as filter.
        Args:
            session: Database async session object.
            filters: Provided pydantic base model.

        Returns:
            Return all objects matching the filter or none.
        """
        if filters:
            filter_dict = filters.model_dump(exclude_unset=True)
        else:
            filter_dict = {}
        logger.debug(f"Поиск нескольких записей по {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            records = result.scalars().all()
            logger.debug(f"Найдено {len(records)} записей")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записей по фильтрам {filter_dict}: {e}")
            raise e

    @classmethod
    async def add(cls, session: AsyncSession, data: BaseModel) -> T:
        data_dict = data.model_dump(exclude_unset=True)
        logger.info(f"Добавление записи {cls.model.__name__} c параметрами: {data_dict}")
        new_instance = cls.model(**data_dict)
        session.add(new_instance)
        try:
            await session.flush()
            logger.info(f"Запись {cls.model.__name__} успешно добавлена")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка добавлении записи: {e}")
            raise e
        return new_instance

    @classmethod
    async def update_one_by_id(cls, session: AsyncSession, data_id: int, data: BaseModel):
        """
        Update a database_url object found by it's id. Updated by pydantic base model.
        Args:
            session: Database async session object.
            data_id: Id of object to update.
            data: New data for update.

        """
        data_dict = data.model_dump(exclude_unset=True)
        logger.debug(
            f"Обновление записи {cls.model.__name__} c ID: {data_id}"
            f"с данными для обновления {data_dict}"
        )
        try:
            record = await session.get(cls.model, data_id)
            for k, v in data_dict.items():
                setattr(record, k, v)
            await session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Не удалось обновить {cls.model.__name__} c ID: {data_id}: {e}")
            raise e

    @classmethod
    async def update_many(
        cls, session: AsyncSession, filter_criteria: BaseModel, values: BaseModel
    ) -> int:
        """
        Universal update many database_url objects by pydantic base model as filter and as new values.
        Args:
            session: Database async session
            filter_criteria: Filters by which objects should be found.
            values: Values by which objects should be updated.

        Returns:
            Rowcount of updated objects.
        """
        filter_dict = filter_criteria.model_dump(exclude_unset=True)
        values_dict = values.model_dump(exclude_unset=True)
        logger.debug(
            f"Обновление несколько записей по фильтрам {filter_dict}, "
            f"данные для обновление {values_dict}"
        )
        try:
            statement = update(cls.model).filter_by(**filter_dict).values(**values_dict)
            result = await session.execute(statement)
            await session.flush()
            return result.rowcount()
        except SQLAlchemyError as e:
            logger.error(
                f"Не удалось обновить объекты по фильтрам {filter_criteria}"
                f"и данными {values_dict}: {e}"
            )
            raise e

    @classmethod
    async def delete_by_id(cls, session: AsyncSession, data_id: int):
        """
        Universal delete one database_url object by it's id.
        Args:
            session:
            data_id:

        Returns:

        """
        logger.debug(f"Поиск записи для удаления {cls.model.__name__} c ID: {data_id}")
        try:
            data = await session.get(cls.model, data_id)
            if data:
                await session.delete(data)
                await session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка удаления записи {cls.model.__name__} c ID: {data_id}: {e}")
            raise

    @classmethod
    async def delete_many(cls, session: AsyncSession, filters: BaseModel | None):
        if filters:
            filters_dict = filters.model_dump(exclude_unset=True)
            statement = delete(cls.model).filter_by(**filters_dict)
            logger.debug(f"Удаление записей по фильтрам {filters_dict}")
        else:
            statement = delete(cls.model)
            logger.debug("Удаление записей")
        try:
            result = await session.execute(statement)
            await session.flush()
            return result.rowcount()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка удаления записей по фильтрам {filters}: {e}")
