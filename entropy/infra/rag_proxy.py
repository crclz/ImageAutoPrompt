from typing import List

import pydantic
import requests

from entropy.domain.models.app_config import AppConfig


class ShowRagRequest(pydantic.BaseModel):
    query_text: str = ""


class RagCandidate(pydantic.BaseModel):
    text: str = ""
    score: float = 0


class ShowRagResponse(pydantic.BaseModel):
    candidates: List[RagCandidate]


class RagProxy:
    @classmethod
    def Rag(cls, request: ShowRagRequest) -> ShowRagResponse:
        rag_service_base_url = AppConfig.read().rag_service_base_url
        assert rag_service_base_url, "rag_service_base_url is empty"

        response = requests.post(f"{rag_service_base_url}/api/show-rag", json=request.model_dump(), timeout=60)
        response.raise_for_status()

        return ShowRagResponse.model_validate_json(response.text)
