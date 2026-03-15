from datetime import datetime
import logging
import os
from pathlib import Path
from threading import Thread
import time
import traceback
from typing import List

import shortuuid

from entropy.domain.models.episode import EpisodeTimestep
from entropy.domain.models.http_dtos import (
    ChooseHighScoresRequest,
    ChooseHighScoresResponse,
    RollbackTimestepRequest,
    RollbackTimestepResponse,
    StartImageProcessingRequest,
    StartImageProcessingResponse,
)
from entropy.domain.models.query_model import EpisodeQueryModel
from entropy.domain.services.llm_parse_service import LlmParseService
from entropy.domain.services.rag_service import RagService
from entropy.infra.comfy_api import ComfyApi
from entropy.infra.episode_repository import EpisodeRepository
from flask import Flask, jsonify, make_response, render_template, request

from entropy.infra.keyed_lock import KeyedLock

_logger = logging.getLogger(__name__)

_episode_timestep_lock = KeyedLock()


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

        episode = EpisodeRepository.get_eposide(name)
        timesteps = EpisodeRepository.get_timesteps_query_model(name)

        # format observation
        for i, timestep in enumerate(timesteps):
            assert i == timestep.i

            if timestep.status == 2:
                ob = "System:"

                # double buffer: if [-1] is running, [-2] must give system message to llm
                if i == len(timesteps) - 2:
                    if timesteps[-1].status == 0:  # running
                        ob += f" timestep={len(timesteps) - 1} 的highscore正在评价中 用户还未给出(由于double-buffer)"

                ob += f" 下列是用户对 timestep={i} 的评价:\n"

                ob += "用户: NewHighScore: "
                if timestep.chosen_highscores:
                    for highscore in timestep.chosen_highscores:
                        llm_info = highscore.format_llm()
                        ob += f"{llm_info}, "
                else:
                    ob += "NO"

                ob += "\n"

                if i >= len(timesteps) - 2:
                    ob += f"System: 接下来请给出timestep={len(timesteps)}的探索"
                ob += "\n"

                timestep.observation = ob

        # display highlight:
        highlight_text = dict()  # key=${timestep}_${image_index}, value=${timestep_when_choose}

        for timestep in timesteps:
            for highscore in timestep.chosen_highscores:
                key = f"{highscore.timestep}_{highscore.image_index}"
                highlight_text[key] = f"HIGH_{timestep.i}"

        for timestep in timesteps:
            for image in timestep.images:
                key = f"{timestep.i}_{image.image_index}"
                if key in highlight_text:
                    image.highlight_text = highlight_text[key]

        # can_process_image
        # 如果最近的2个timestep，有任何1个进行了评价，那么都可以继续process.
        can_process_image = 0
        if episode.can_process_image():
            can_process_image = 1

        return EpisodeQueryModel(timesteps=timesteps, can_process_image=can_process_image)

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

        # if request.timestep != len(episode.timesteps) - 1:
        #     raise ValueError(f"wrong timestep. expected: {len(episode.timesteps) - 1}, actual: {request.timestep}")

        to_be_chosen = episode.get_to_be_chosen()
        if to_be_chosen is None:
            raise ValueError("cannot choose highscore")

        # choose

        to_be_chosen.chosen_highscores = request.highscores
        to_be_chosen.status = 2  # 1,2 => 2. restrictions of 1,2 is in episode.get_to_be_chosen

        # save
        EpisodeRepository.save_episode(request.name, episode)

        return ChooseHighScoresResponse()

    @classmethod
    def start_image_processing_wrapper(cls, episode_name: str):
        try:
            assert episode_name

            req = StartImageProcessingRequest.model_validate(request.get_json())
            req.episode_name = episode_name

            assert episode_name

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

        danbooru_search_query_list = LlmParseService.parse_danbooru_search(request.exploration_output)

        if not positives:
            raise ValueError("parse exploration_output failed")

        # check positives
        episode = EpisodeRepository.get_eposide(request.episode_name)

        if not episode.can_process_image():
            raise ValueError("cannot process image")

        # create new timestep
        timestep_i = len(episode.timesteps)

        # NOTE: only timestep is locked. update episode should get-modify-save

        key = f"{request.episode_name}:{timestep_i}"
        episode.timesteps.append(EpisodeTimestep(i=timestep_i, rag_wip=(1 if danbooru_search_query_list else 0)))
        EpisodeRepository.save_episode(request.episode_name, episode)

        del episode  # cannot reuse, because stale

        def complete_hook(image_index: int, image_bytes: bytes) -> None:
            # save so that web page can see the picture
            pic_save_path = EpisodeRepository.pic_path(request.episode_name, timestep_i, image_index)
            pic_save_path.write_bytes(image_bytes)

        def thread_function():
            with _episode_timestep_lock.lock(key, 0.5):
                t0 = datetime.now()
                ComfyApi.run_many(base_url, template_json, positives, negatives, complete_hook=complete_hook)

                dt = (datetime.now() - t0).total_seconds()
                _logger.info(f"run_many takes {dt:.1f} seconds")

                episode = EpisodeRepository.get_eposide(request.episode_name)
                episode.timesteps[timestep_i].status = 1

                EpisodeRepository.save_episode(request.episode_name, episode)

        def danbooru_search():
            cls.danbooru_search_and_save(request.episode_name, timestep_i, danbooru_search_query_list)

        if True:
            th = Thread(target=thread_function, daemon=True)
            th.start()

            danbooru_search_thread = Thread(target=danbooru_search, daemon=True)
            danbooru_search_thread.start()

            if join:
                th.join()
                danbooru_search_thread.join()

        return StartImageProcessingResponse()

    @classmethod
    def danbooru_search_and_save(cls, episode_name: str, timestep: int, query_list: List[str]) -> None:
        # do search before modify episode
        danbooru_search_outputs = []

        for query in query_list:
            tags, scores = RagService.do_rag(query)

            danbooru_search_outputs += f"search {query} => " + ",".join(tags)

        danbooru_search_result = "\n".join(danbooru_search_outputs) + "\n"

        # update episode
        episode = EpisodeRepository.get_eposide(episode_name)
        episode.timesteps[timestep].rag_wip = 0
        episode.timesteps[timestep].rag_result = danbooru_search_result

    @classmethod
    def rollback_timestep_wrapper(cls, episode_name: str):
        try:
            assert episode_name

            req = RollbackTimestepRequest.model_validate(request.get_json())
            req.episode_name = episode_name

            assert episode_name

            resp = cls.rollback_timestep(req)

            data_object = resp.model_dump()
            return data_object
        except Exception as e:
            _logger.exception("start_image_processing_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def rollback_timestep(cls, request: RollbackTimestepRequest) -> RollbackTimestepResponse:
        episode = EpisodeRepository.get_eposide(request.episode_name)

        if not episode.timesteps:
            raise ValueError("episode empty, cannot rollback")

        rolled_i = len(episode.timesteps) - 1

        episode_name = request.episode_name
        assert episode_name, "episode_name is empty"

        key = f"{episode_name}:{rolled_i}"

        if _episode_timestep_lock.is_locked(key):
            raise ValueError(f"episode timestep locked ({key}). kill the program and restart")

        with _episode_timestep_lock.lock(key, timeout=0.5):
            episode.timesteps.pop()

            ts_pics = EpisodeRepository.timestep_pics(request.episode_name, rolled_i)

            rollback_time = time.time().__int__()

            for pic in ts_pics:
                # move pic to pic.parent/trash/*_uuid.png
                trash_dir = pic.parent / "trash"
                trash_dir.mkdir(exist_ok=True)

                new_name = pic.name.removesuffix(".png") + f"_rollback_{rollback_time}.png"

                dst = trash_dir / new_name

                pic.rename(dst)

            EpisodeRepository.save_episode(request.episode_name, episode)

            return RollbackTimestepResponse()
