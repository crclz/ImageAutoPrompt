
import pydantic
import requests

from entropy.domain.models.app_config import AppConfig


class ShowRagRequest(pydantic.BaseModel):
    query_text: str = ""


class RagCandidate(pydantic.BaseModel):
    text: str = ""
    score: float = 0


class ShowRagResponse(pydantic.BaseModel):
    candidates: list[RagCandidate]


class RagProxy:
    @classmethod
    def Rag(cls, request: ShowRagRequest) -> ShowRagResponse:
        port = AppConfig.read().port

        response = requests.post(f"http://127.0.0.1:{port}/api/show-rag", json=request.model_dump(), timeout=60)
        response.raise_for_status()

        return ShowRagResponse.model_validate_json(response.text)
