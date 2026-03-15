from typing import List

import pydantic


class ImagePointer(pydantic.BaseModel):
    timestep: int = 0
    image_index: int = 0  # llm output should start from 0

    def format_llm(self) -> str:
        return f"timestep_{self.timestep}_image[{self.image_index}]"


class EpisodeTimestep(pydantic.BaseModel):
    i: int = 0

    status: int = 0
    """0=image processing, 1=image done, 2=high score chosen"""

    chosen_highscores: List[ImagePointer] = []


class Episode(pydantic.BaseModel):
    create_time: int = 0
    timesteps: List[EpisodeTimestep] = []

    def can_process_image(self) -> bool:
        last_two_status = reversed([p.status for p in self.timesteps[-2:]])
        if any([p for p in last_two_status if p == 2]):
            return True
        return False
