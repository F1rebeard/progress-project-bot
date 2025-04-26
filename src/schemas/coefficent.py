from pydantic import BaseModel, ConfigDict

from src.database.models import ProfileExercise, User, UserProfileResult


class ExerciseNameFilter(BaseModel):
    name: str


class CoefficientData(BaseModel):
    """
    Data required for coefficient calculations.
    """

    user: User | None = None
    weight: float | None = None
    coefficient_exercise: ProfileExercise | None = None
    base_exercise: ProfileExercise | None = None
    base_result: UserProfileResult | None = None
    workout_weight: float = 0.0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def is_complete(self) -> bool:
        """
        Check if all required data is complete.

        Returns:
            True if all data is collected, else False.
        """
        return all(
            [
                self.user,
                self.weight,
                self.coefficient_exercise,
                self.base_exercise,
                self.base_result,
            ]
        )
