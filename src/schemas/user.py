from pydantic import BaseModel, Field

from src.database.models.user import Gender, UserLevel, UserRole


class UserCreateSchema(BaseModel):
    telegram_id: int
    username: str | None
    role: UserRole = Field(default=UserRole.USER)


class UserUpdateSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    email: str | None = None
    gender: Gender | None = None
    level: UserLevel | None = None

