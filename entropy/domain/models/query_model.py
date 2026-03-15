# frontend models


from typing import List

import pydantic

from entropy.domain.models.episode import ImagePointer


class ImageQueryModel(pydantic.BaseModel):
    image_index: int = 0
    url: str = ""

    highlight_text: str = ""


class TimestepQueryModel(pydantic.BaseModel):
    i: int = 0
    images: List[ImageQueryModel] = []
    chosen_highscores: List[ImagePointer] = []
    status: int = 0
    observation: str = ""  # timestep=i, 用户: NewHighScore: xxx

    rag_wip: int = 0
    rag_result: str = ""

    def sort_images(self) -> None:
        self.images.sort(key=lambda x: x.image_index)


class EpisodeQueryModel(pydantic.BaseModel):
    can_process_image: int = 0
    timesteps: List[TimestepQueryModel] = []
