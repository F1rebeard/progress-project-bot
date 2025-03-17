from functools import wraps

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import database_url, settings

engine = create_async_engine(url=database_url, echo=settings.DEBUG)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)


def connection(isolation_level=None, commit: bool = True):
    """
    Decorator for database_url session with management of isolation level and commit.
    Args:
        isolation_level: isolation level of transaction
         (READ COMMITTED, SERIALIZABLE, REPEATABLE READ)
        commit: if True, commit the changes to database_url after method calling.

    """

    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            async with async_session_maker() as session:
                try:
                    # Setup isolation level if given
                    if isolation_level:
                        await session.execute(
                            text(f"Set TRANSACTION ISOLATION LEVEL {isolation_level}")
                        )
                    result = await method(*args, session=session, **kwargs)
                    if commit:
                        await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    raise e
                finally:
                    await session.close()

        return wrapper

    return decorator


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @classmethod
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
