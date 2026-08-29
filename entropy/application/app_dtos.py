
import pydantic

from entropy.domain.models.episode import ImagePointer


class ApiResponse(pydantic.BaseModel):
    """所有 API Response 的统一基类：code + message 必带，业务字段平铺。"""

    code: int = 0  # 0=成功；-1=未分类错误；内层有权返回其他值
    message: str = ""


class ChooseHighScoresRequest(pydantic.BaseModel):
    name: str = ""
    # timestep: int = 0  # for integrity check
    highscores: list[ImagePointer] = []
    overwrite: int = 0  # 1=确认覆盖已反馈的 timestep（前端二次确认后传递）


class ChooseHighScoresResponse(ApiResponse):
    pass


class StartImageProcessingRequest(pydantic.BaseModel):
    episode_name: str = ""
    timestep_draft: str = ""


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
    candidates: list[RagCandidate]


class GetEpisodeListRequest(pydantic.BaseModel):
    pass


class EpisodeListItem(pydantic.BaseModel):
    name: str = ""
    create_time: int = 0


class GetEpisodeListResponse(ApiResponse):
    episodes_list: list[EpisodeListItem] = []


class CreateEpisodeRequest(pydantic.BaseModel):
    name: str = ""
    workflow: str = ""  # comfy workflow 相对路径；空时回退 app_config 的默认工作流
    invalid_tag_budget: int = 0  # 无效 tag 预算；0=不校验（web 端不传，CLI 必传）


class CreateEpisodeResponse(ApiResponse):
    pass
