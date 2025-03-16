from datetime import date

from pydantic import BaseModel


class BiometricUpdateSchema(BaseModel):
    height: int | None = None
    weight: float | None = None
    birthday: date | None = None


class BiometricCreateSchema(BiometricUpdateSchema):
    user_id: int
