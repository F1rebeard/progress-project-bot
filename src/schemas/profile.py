from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from src.database.models.profile import ResultType
from src.database.models.user import UserLevel


class ExerciseStandardFilter(BaseModel):
    exercise_id: int
    user_level: UserLevel


class ProfileResultSubmitSchema(BaseModel):
    """
    Schema for submitting a new result for exercise.
    """

    exercise_id: int
    result_value: float
    date: datetime = Field(default_factory=datetime.now)

    @field_validator("result_value")
    @classmethod
    def validate_positive_result_value(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Result value cannot be negative")
        return value


class ProfileResultValidatedSchema(ProfileResultSubmitSchema):
    """
    Schema for validated exercise result with additional validation based on standards.
    """

    user_id: int
    gender_standards: dict = Field(exclude=True)
    exercise_info: dict = Field(exclude=True)

    @model_validator(mode="after")
    def validate_result_against_standards(self):
        """Validate result against gender-specific standards."""
        v = self.result_value
        gender_standards = self.gender_standards
        exercise_info = self.exercise_info

        if not gender_standards or not exercise_info:
            return self

        min_value = gender_standards.get("min_value")
        max_value = gender_standards.get("max_value")
        is_time_based = exercise_info.get("is_time_based", False)
        result_type = exercise_info.get("result_type")

        # For time-based exercises with ASAP_TIME result type, lower is better
        if is_time_based and result_type == ResultType.ASAP_TIME:
            if max_value is not None and v > max_value:
                raise ValueError(f"Time is too slow (max {max_value})")
            if min_value is not None and v < min_value:
                raise ValueError(f"Time is unrealistically fast (min {min_value})")
        # For other result types, higher is better
        else:
            if min_value is not None and v < min_value:
                raise ValueError(f"Result is too low (min {min_value})")
            if max_value is not None and v > max_value:
                raise ValueError(f"Result is unrealistically high (max {max_value})")

        return self


class ProfileResultCompleteSchema(BaseModel):
    """
    Complete schema with all fields needed for saving a new exercise result.
    """

    user_id: int
    exercise_id: int
    result_value: float
    date: datetime = Field(default_factory=datetime.now)
