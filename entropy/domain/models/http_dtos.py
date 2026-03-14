from typing import List

import pydantic

from entropy.domain.models.episode import ImagePointer


class ChooseHighScoresRequest(pydantic.BaseModel):
    name: str = ""
    timestep: int = 0  # for integrity check
    highscores: List[ImagePointer] = []


class ChooseHighScoresResponse(pydantic.BaseModel):
    pass
