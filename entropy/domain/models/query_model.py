# frontend models



import pydantic

from entropy.domain.models.episode import ImagePointer


class ImageQueryModel(pydantic.BaseModel):
    image_index: int = 0
    url: str = ""
    local_abs_path: str = ""

    highlight_text: str = ""


class TimestepQueryModel(pydantic.BaseModel):
    i: int = 0
    images: list[ImageQueryModel] = []
    chosen_highscores: list[ImagePointer] = []
    status: int = 0
    observation: str = ""  # timestep=i, 用户: NewHighScore: xxx

    initial_md_prefix: str = ""

    diff_positive_tags: str = ""
    diff_negative_tags: str = ""

    invalid_tags: str = ""

    error: str = ""
    stacktrace: str = ""

    def sort_images(self) -> None:
        self.images.sort(key=lambda x: x.image_index)


class EpisodeQueryModel(pydantic.BaseModel):
    can_process_image: int = 0
    timesteps: list[TimestepQueryModel] = []
