from typing import List, Optional

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

    rag_result: str = ""


class Episode(pydantic.BaseModel):
    create_time: int = 0
    timesteps: List[EpisodeTimestep] = []

    def can_process_image(self) -> bool:
        if len(self.timesteps) <= 2:
            return True

        last_two_status = reversed([p.status for p in self.timesteps[-2:]])
        if any([p for p in last_two_status if p == 2]):
            return True
        return False

    def get_to_be_chosen(self) -> Optional[EpisodeTimestep]:
        """
        返回需要进行评最高分的timestep.
        """

        last_two_timesteps = reversed(self.timesteps[-2:])

        # 1和2都可以进行最高分选择，其中2是覆盖
        for timestep in last_two_timesteps:
            if timestep.status in (1, 2):  # 优先打没打分的
                return timestep

        return None
