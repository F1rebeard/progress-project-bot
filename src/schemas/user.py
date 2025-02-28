from pydantic import BaseModel, Field

from src.database.models.user import UserRole


class UserCreateSchema(BaseModel):
    telegram_id: int
    username: str | None
    role: UserRole = Field(default=UserRole.USER)


class UserUpdateSchema(BaseModel):
    pass
