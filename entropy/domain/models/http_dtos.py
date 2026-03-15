from typing import List

import pydantic

from entropy.domain.models.episode import ImagePointer


class ChooseHighScoresRequest(pydantic.BaseModel):
    name: str = ""
    # timestep: int = 0  # for integrity check
    highscores: List[ImagePointer] = []


class ChooseHighScoresResponse(pydantic.BaseModel):
    pass


class StartImageProcessingRequest(pydantic.BaseModel):
    episode_name: str = ""
    exploration_output: str = ""


class StartImageProcessingResponse(pydantic.BaseModel):
    pass


class RollbackTimestepRequest(pydantic.BaseModel):
    episode_name: str = ""


class RollbackTimestepResponse(pydantic.BaseModel):
    pass


class ShowRagRequest(pydantic.BaseModel):
    query_text: str = ""


class RagCandidate(pydantic.BaseModel):
    text: str = ""
    score: float = 0


class ShowRagResponse(pydantic.BaseModel):
    candidates: List[RagCandidate]
