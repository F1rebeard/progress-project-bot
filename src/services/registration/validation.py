from datetime import date, datetime
from typing import ClassVar, Any, Dict

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ValidationInfo

from src.database.models.user import UserLevel, Gender


class ValidationModel(BaseModel):
    """Base model with custom error messages functionality"""

    # Class variable to store error messages
    error_messages: ClassVar[Dict[str, str]] = {}

    @model_validator(mode="after")
    def check_custom_constraints(self, info: ValidationInfo) -> "ValidationModel":
        """Add custom validation messages to validation errors"""
        return self


class FirstNameSchema(ValidationModel):
    first_name: str = Field(min_length=2, max_length=30, pattern=r"^[A-ZА-ЯЁ][a-zа-яё]+$")

    error_messages = {
        "min_length": "Имя должно содержать минимум 2 символа",
        "max_length": "Имя должно содержать максимум 30 символов",
        "pattern": "Имя должно начинаться с заглавной буквы и содержать только буквы"
    }

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        if len(value) < 2:
            raise ValueError(cls.error_messages["min_length"])
        if len(value) > 30:
            raise ValueError(cls.error_messages["max_length"])
        if not value[0].isupper() or not value[1:].islower():
            raise ValueError(cls.error_messages["pattern"])
        return value



class LastNameSchema(BaseModel):
    last_name: str = Field(min_length=2, max_length=30, pattern=r"^[A-ZА-ЯЁ][a-zа-яё]+$")


class  EmailSchema(BaseModel):
    email: EmailStr


class GenderSchema(BaseModel):
    gender: Gender


class LevelSchema(BaseModel):
    level: UserLevel


class HeightSchema(BaseModel):
    height: float = Field(..., ge=100, le=250)


class WeightSchema(BaseModel):
    weight: float = Field(..., ge=30, le=180)


class BirthdaySchema(BaseModel):
    birthday: date

    @classmethod
    def parse_date_string(cls, date_str: str) -> "BirthdaySchema":
        """
        Parse a date string in DD.MM.YYYY format and validate it.

        Args:
            date_str: Date string in DD.MM.YYYY format

        Returns:
            Validated BirthDateSchema instance

        Raises:
            ValueError: If the date string is not in the correct format or the date is invalid
        """
        try:
            birth_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            return cls(birthday=birth_date)
        except ValueError:
            raise ValueError("Неверный формат даты, нужен ДД.ММ.ГГГГ")

    @field_validator("birthday", mode="before")
    @classmethod
    def validate_age(cls, birth_date: date) -> date:
        """
        Validates user age withing acceptable range.

        Args:
            birth_date: Date of birth to validate

        Returns:
            birth_date: The validated birthdate

        Raises:
            ValueError: If the user's age is not within the acceptable range.
        """
        min_age: int = 16
        max_age: int = 100
        today = date.today()
        age = (today - birth_date).days // 365
        if not min_age <= age <= max_age:
            raise ValueError(f"Введи корректную дату рождения, пожалуйста")
        return birth_date