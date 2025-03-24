from src.dao import BaseDAO
from src.database.models import (
    ExerciseStandard,
    ProfileCategory,
    ProfileExercise,
    UserProfileResult,
)


class ProfileCategoryDAO(BaseDAO):
    model = ProfileCategory


class ProfileExerciseDAO(BaseDAO):
    model = ProfileExercise


class ExerciseStandardDAO(BaseDAO):
    model = ExerciseStandard


class UserProfileResultDAO(BaseDAO):
    model = UserProfileResult
