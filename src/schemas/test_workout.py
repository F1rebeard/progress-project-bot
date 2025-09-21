from pydantic import BaseModel


class TestWorkoutDayFilter(BaseModel):
    """
    Filter for finding a test workout by day number.
    """
    day_number: int


class TestWorkoutUpdateSchema(BaseModel):
    """
    Schema for updating a test workout.
    """
    description: str


class TestWorkoutCreateSchema(TestWorkoutUpdateSchema):
    """
    Schema for creating a new test workout.
    """
    day_number: int
    description: str