from typing import List

import pydantic

from entropy.domain.models.episode import ImagePointer


class ApiResponse(pydantic.BaseModel):
    """所有 API Response 的统一基类：code + message 必带，业务字段平铺。"""

    code: int = 0  # 0=成功；-1=未分类错误；内层有权返回其他值
    message: str = ""


class ChooseHighScoresRequest(pydantic.BaseModel):
    name: str = ""
    # timestep: int = 0  # for integrity check
    highscores: List[ImagePointer] = []


class ChooseHighScoresResponse(ApiResponse):
    pass


class StartImageProcessingRequest(pydantic.BaseModel):
    episode_name: str = ""
    exploration_output: str = ""


class StartImageProcessingResponse(ApiResponse):
    pass


class RollbackTimestepRequest(pydantic.BaseModel):
    episode_name: str = ""


class RollbackTimestepResponse(ApiResponse):
    pass


class ShowRagRequest(pydantic.BaseModel):
    query_text: str = ""


class RagCandidate(pydantic.BaseModel):
    text: str = ""
    score: float = 0


class ShowRagResponse(ApiResponse):
    candidates: List[RagCandidate]


class GetEpisodeListRequest(pydantic.BaseModel):
    pass


class EpisodeListItem(pydantic.BaseModel):
    name: str = ""
    create_time: int = 0


class GetEpisodeListResponse(ApiResponse):
    episodes_list: List[EpisodeListItem] = []


class CreateEpisodeRequest(pydantic.BaseModel):
    name: str = ""


class CreateEpisodeResponse(ApiResponse):
    pass
