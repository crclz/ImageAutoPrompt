from datetime import datetime
import logging
import os
from pathlib import Path
from threading import Thread
import traceback

from entropy.domain.models.episode import EpisodeTimestep
from entropy.domain.models.http_dtos import (
    ChooseHighScoresRequest,
    ChooseHighScoresResponse,
    StartImageProcessingRequest,
    StartImageProcessingResponse,
)
from entropy.domain.models.query_model import EpisodeQueryModel
from entropy.domain.services.llm_parse_service import LlmParseService
from entropy.infra.comfy_api import ComfyApi
from entropy.infra.episode_repository import EpisodeRepository
from flask import Flask, jsonify, make_response, render_template, request

_logger = logging.getLogger(__name__)


class EpisodeHandler:
    @classmethod
    def episodes_list_page(cls) -> None:
        """
        In this page, episodes are listed. Order by create_time desc.
        Episodes are managed using folder structure.
        Main data is in episode.json
        """
        raise NotImplementedError()

    @classmethod
    def new_episode(cls) -> None:
        """
        start new episode
        """
        raise NotImplementedError()

    @classmethod
    def episode_page_wrapper(cls, episode_name):
        return render_template("episode.html", episode_name=episode_name)

    @staticmethod
    def wrap_api_exception(e: Exception):
        err_data = {
            "message": str(e),
            # "stack": traceback.format_exc(),
        }

        return make_response(jsonify(err_data), 400)

    @classmethod
    def get_episode_data_wrapper(cls, episode_name: str):
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel json
        """
        try:
            data = cls.get_episode_data(episode_name)
            data_object = data.model_dump()
            return data_object
        except Exception as e:
            _logger.exception("get_episode_data_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def get_episode_data(cls, name: str) -> EpisodeQueryModel:
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel
        """

        timesteps = EpisodeRepository.get_timesteps_query_model(name)

        # format observation
        for timestep in timesteps:
            if timestep.status == 2:
                ob = f"timestep={timestep.i}\n"

                ob += "用户: NewHighScore: "
                if timestep.chosen_highscores:
                    for highscore in timestep.chosen_highscores:
                        llm_info = highscore.format_llm()
                        ob += f"{llm_info}, "
                else:
                    ob += "NO"

                ob += "\n"

                timestep.observation = ob

        # display highlight:
        highlight_text = dict()  # key=${timestep}_${image_index}, value=${timestep_when_choose}

        for timestep in timesteps:
            for highscore in timestep.chosen_highscores:
                key = f"{highscore.timestep}_{highscore.image_index}"
                highlight_text[key] = f"HIGH {timestep.i}"

        for timestep in timesteps:
            for image in timestep.images:
                key = f"{timestep.i}_{image.image_index}"
                if key in highlight_text:
                    image.highlight_text = highlight_text[key]

        return EpisodeQueryModel(timesteps=timesteps)

    @classmethod
    def choose_high_scores_wrapper(cls, episode_name):
        try:
            assert episode_name, "episode_name is empty"

            req = ChooseHighScoresRequest.model_validate(request.get_json())
            req.name = episode_name

            resp = cls.choose_high_scores(req)
            data_object = resp.model_dump()
            return data_object
        except Exception as e:
            _logger.exception("choose_high_scores_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def choose_high_scores(cls, request: ChooseHighScoresRequest) -> ChooseHighScoresResponse:
        """
        change EpisodeTimestep.status from 1 to 2.
        2 can submit.

        args:
        - timestep: for integrity check
        """

        episode = EpisodeRepository.get_eposide(request.name)

        if request.timestep != len(episode.timesteps) - 1:
            raise ValueError(f"wrong timestep. expected: {len(episode.timesteps) - 1}, actual: {request.timestep}")

        newest_timestep = episode.timesteps[len(episode.timesteps) - 1]

        if newest_timestep.status not in (1, 2):
            raise ValueError(f"cannot choose high score. newest_timestep.status: {newest_timestep.status}")

        # choose
        # support no high score
        # if not request.highscores:
        #     raise ValueError("request.highscores is empty")

        newest_timestep.chosen_highscores = request.highscores
        newest_timestep.status = 2

        # save
        EpisodeRepository.save_episode(request.name, episode)

        return ChooseHighScoresResponse()

    @classmethod
    def start_image_processing_wrapper(cls, episode_name: str):
        try:
            assert episode_name

            req = StartImageProcessingRequest.model_validate(request.get_json())
            req.episode_name = episode_name

            resp = cls.start_image_processing(req)
            data_object = resp.model_dump()
            return data_object
        except Exception as e:
            _logger.exception("start_image_processing_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def start_image_processing(cls, request: StartImageProcessingRequest, join=False) -> StartImageProcessingResponse:
        """
        create new timestep. when done, change status from 0 to 1
        change EpisodeTimestep.status from 0 to 1.
        when failure, rollback
        """

        # base url
        base_url = os.environ.get("COMFY_BASE_URL")
        assert base_url, "COMFY_BASE_URL not provided"
        assert base_url.startswith("http"), "COMFY_BASE_URL should start with http"

        # template json
        json_file = "comfyui_template.json"
        if not Path(json_file).exists():
            raise ValueError(f"not exist: {json_file}")

        template_json = Path(json_file).read_text("utf8")

        # parse llm
        assert request.exploration_output, "exploration_output is empty"

        positives, negatives = LlmParseService.parse_exploration_output(request.exploration_output)

        if not positives:
            raise ValueError("parse exploration_output failed")

        # check positives
        episode = EpisodeRepository.get_eposide(request.episode_name)

        if episode.timesteps:
            last_status = episode.timesteps[-1].status
            if last_status != 2:
                raise ValueError(f"last timestep status != 2. actual: {last_status}")

        # create new timestep
        timestep_i = len(episode.timesteps)

        episode.timesteps.append(
            EpisodeTimestep(
                i=timestep_i,
            )
        )
        EpisodeRepository.save_episode(request.episode_name, episode)

        def complete_hook(image_index: int, image_bytes: bytes) -> None:
            # save so that web page can see the picture
            pic_save_path = EpisodeRepository.pic_path(request.episode_name, timestep_i, image_index)
            pic_save_path.write_bytes(image_bytes)

        def thread_function():
            try:
                t0 = datetime.now()
                ComfyApi.run_many(base_url, template_json, positives, negatives, complete_hook=complete_hook)

                dt = (datetime.now() - t0).total_seconds()
                _logger.info(f"run_many takes {dt:.1f} seconds")

                episode.timesteps[-1].status = 1

                EpisodeRepository.save_episode(request.episode_name, episode)

            except (Exception, KeyboardInterrupt):
                _logger.exception("start_image_processing has error")

                episode.timesteps.pop()
                EpisodeRepository.save_episode(request.episode_name, episode)

                raise

        if True:
            th = Thread(target=thread_function)
            th.start()

            if join:
                th.join()

        return StartImageProcessingResponse()
