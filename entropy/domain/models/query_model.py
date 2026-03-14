# frontend models


from typing import List

import pydantic

from entropy.domain.models.episode import ImagePointer


class ImageQueryModel(pydantic.BaseModel):
    image_index: int = 0
    url: str = ""


class TimestepQueryModel(pydantic.BaseModel):
    i: int = 0
    images: List[ImageQueryModel] = []
    chosen_highscores: List[ImagePointer] = []
    status: int = 0

    def sort_images(self) -> None:
        self.images.sort(key=lambda x: x.image_index)


class EpisodeQueryModel(pydantic.BaseModel):
    timesteps: List[TimestepQueryModel] = []
