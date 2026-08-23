
import pydantic


class ExplorationAbstract(pydantic.BaseModel):
    type: str = ""
    description: str = ""
    keywords: list[str] = []


class TimestepDraftParseResult(pydantic.BaseModel):
    """parse_timestep_draft 的解析结果。"""

    positives: list[str] = []
    negatives: list[str] = []
    loras: list[str] = []
    is_friendly: bool = False
