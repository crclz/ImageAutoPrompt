import logging

from flask import render_template, request

from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.http_dtos import RagCandidate, ShowRagRequest, ShowRagResponse
from entropy.domain.services.rag_service import RagService

_logger = logging.getLogger(__name__)


class RagHandler:
    @classmethod
    def rag_page_wrapper(cls):
        return render_template("rag.html")

    @classmethod
    def show_rag_wrapper(cls):
        """
        User can do rag on danbooru tags on web page
        """
        try:
            req = ShowRagRequest.model_validate(request.get_json())

            if not req.query_text:
                raise ValueError("query_text is empty")

            texts, scores = RagService.rag_simple(req.query_text, 20)

            candidates = []

            for text, score in zip(texts, scores):
                candidates.append(RagCandidate(text=text, score=score))

            response = ShowRagResponse(candidates=candidates)

            data_object = response.model_dump()
            return data_object
        except Exception as e:
            _logger.exception("show_rag_wrapper error")
            return EpisodeHandler.wrap_api_exception(e)
