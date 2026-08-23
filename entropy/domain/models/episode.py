
import pydantic


class ImagePointer(pydantic.BaseModel):
    timestep: int = 0
    image_index: int = 0  # llm output should start from 0

    def format_llm(self) -> str:
        return f"timestep_{self.timestep}_image[{self.image_index}]"


class ImagePrompt(pydantic.BaseModel):
    positive: str
    negative: str
    lora: str = ""  # 可选，形如 "<lora:xxx:1.0> <lora:yyy:0.9>"；为空表示无 lora


class EpisodeTimestep(pydantic.BaseModel):
    i: int = 0

    status: int = 0
    """0=image processing, 1=image done, 2=high score chosen"""

    chosen_highscores: list[ImagePointer] = []

    prompts: list[ImagePrompt] = []



class Episode(pydantic.BaseModel):
    create_time: int = 0
    timesteps: list[EpisodeTimestep] = []

    def can_process_image(self) -> bool:
        """上一个 timestep 需跑完且已提交反馈（status==2），才能开始下一个"""
        if not self.timesteps:
            return True
        return self.timesteps[-1].status == 2

    def get_feedbackable_timestep(self) -> EpisodeTimestep | None:
        """
        返回当前可提交反馈的 timestep：最新的一个（status 1=跑完待反馈, 2=已反馈可覆盖）
        """
        if not self.timesteps:
            return None

        last = self.timesteps[-1]
        if last.status in (1, 2):
            return last
        return None
