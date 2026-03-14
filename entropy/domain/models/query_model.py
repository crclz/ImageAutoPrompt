# frontend models


from typing import List

import pydantic

from entropy.domain.models.episode import ImagePointer


class ImageQueryModel(pydantic.BaseModel):
    url: str = ""


class TimestepQueryModel(pydantic.BaseModel):
    i: int = 0
    images: List[ImageQueryModel] = []
    choosed_highscore: List[ImagePointer] = []


class EpisodeQueryModel(pydantic.BaseModel):
    timesteps: List[TimestepQueryModel] = []
