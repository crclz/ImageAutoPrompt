import logging
import traceback

from entropy.domain.models.http_dtos import ChooseHighScoresRequest, ChooseHighScoresResponse
from entropy.domain.models.query_model import EpisodeQueryModel
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

    # @classmethod
    # def episode_page(cls):
    #     """
    #     this page accept query parameter: name
    #     and show:
    #     - timesteps and images
    #     - high score images (highlight)

    #     these data are refreshed frequently, by polling get_episode_data via page
    #     """
    #     raise NotImplementedError()

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
        change EpisodeTimestep.status from 1 to 2

        args:
        - timestep: for integrity check
        """

        episode = EpisodeRepository.get_eposide(request.name)

        if request.timestep != len(episode.timesteps) - 1:
            raise ValueError(f"wrong timestep. expected: {len(episode.timesteps) - 1}, actual: {request.timestep}")

        newest_timestep = episode.timesteps[len(episode.timesteps) - 1]

        if newest_timestep.status != 1:
            raise ValueError(f"cannot choose high score. newest_timestep.status: {newest_timestep.status}")

        # choose
        if not request.highscores:
            raise ValueError("request.highscores is empty")

        newest_timestep.chosen_highscores = request.highscores
        newest_timestep.status = 2

        # save
        EpisodeRepository.save_episode(request.name, episode)

        return ChooseHighScoresResponse()

    @classmethod
    def get_timestep_observation(cls):
        """
        return a string e.g.
        timestep=15
        user: NewHighScore: timestep_14_image[0]
        """
        raise NotImplementedError()

    @classmethod
    def start_image_processing(cls):
        """
        change EpisodeTimestep.status from 0 to 1.
        when done, change EpisodeTimestep.status from 1 to 2.
        user can force state go back to 0.
        """
        raise NotImplementedError()
