from typing import List

import pydantic


class ImagePointer(pydantic.BaseModel):
    timestep: int = 0
    image_index: int = 0  # llm output should start from 0

    def format_llm(self) -> str:
        return f"timestep_{self.timestep}_image[{self.image_index}]"


class EpisodeTimestep(pydantic.BaseModel):
    i: int = 0
    current_high_scores: List[ImagePointer] = []


class Episode(pydantic.BaseModel):
    timesteps: List[EpisodeTimestep] = []
