import logging
import re
import time
from pathlib import Path

from flask import jsonify, make_response, render_template, request

from entropy.application.app_dtos import (
    ChooseHighScoresRequest,
    ChooseHighScoresResponse,
    CreateEpisodeRequest,
    CreateEpisodeResponse,
    EpisodeListItem,
    GetEpisodeListRequest,
    GetEpisodeListResponse,
    RollbackTimestepRequest,
    RollbackTimestepResponse,
    StartImageProcessingRequest,
    StartImageProcessingResponse,
)
from entropy.domain.models.episode import Episode
from entropy.domain.models.error_code import ErrorCode
from entropy.domain.models.query_model import EpisodeQueryModel
from entropy.domain.services.episode_heartbeat_service import EpisodeHeartbeatService
from entropy.domain.services.tag_checker import TagChecker
from entropy.domain.services.timestep_draft_consumption_service import TimestepDraftConsumptionService
from entropy.infra.cancellation import send_cancel
from entropy.infra.episode_repository import EpisodeRepository

_logger = logging.getLogger(__name__)


class EpisodeHandler:
    @classmethod
    def episode_page_wrapper(cls, episode_name):
        return render_template("episode.html", episode_name=episode_name)

    @staticmethod
    def wrap_api_exception(e: Exception):
        err_data = {
            "code": -1,  # -1 = 未分类错误
            "message": str(e),
            # "stack": traceback.format_exc(),
        }

        return make_response(jsonify(err_data), 400)

    @staticmethod
    def wrap_api_ok(data: dict | None = None) -> dict:
        """
        统一成功响应结构: {code: 0, message: "", ...业务字段平铺}
        """
        resp = {"code": 0, "message": ""}
        if data:
            resp.update(data)
        return resp

    @staticmethod
    def wrap_api_response(resp):
        """
        统一响应: Response model 自带 code/message。
        code==0 -> HTTP 200; code!=0 -> HTTP 400
        """
        data = resp.model_dump()
        status = 200 if data.get("code", 0) == 0 else 400
        return make_response(jsonify(data), status)

    @classmethod
    def get_episode_data_wrapper(cls, episode_name: str):
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel json
        """
        try:
            data = cls.get_episode_data(episode_name)
            data_object = data.model_dump()
            return cls.wrap_api_ok(data_object)
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

        # diff tags
        for i, timestep in enumerate(timesteps):
            if i > 0:
                last_positive_tags, last_negative_tags = TagChecker.all_tags_in_timestep(episode.timesteps[i - 1])
                this_positive_tags, this_negative_tags = TagChecker.all_tags_in_timestep(episode.timesteps[i])

                timestep.diff_positive_tags = ", ".join(list(set(this_positive_tags) - set(last_positive_tags)))
                timestep.diff_negative_tags = ", ".join(list(set(this_negative_tags) - set(last_negative_tags)))

        # invalid tags
        for i, timestep in enumerate(timesteps):
            this_positive_tags, this_negative_tags = TagChecker.all_tags_in_timestep(episode.timesteps[i])
            all_tags = this_positive_tags + this_negative_tags
            all_tags = list(set(all_tags))

            timestep.invalid_tags = ", ".join([p for p in all_tags if not TagChecker.exist_tag(p)])

        # display highlight:
        highlight_text = {}  # key=${timestep}_${image_index}, value=${timestep_when_choose}

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

        is_really_running = 1 if EpisodeHeartbeatService.is_really_running(name) else 0

        return EpisodeQueryModel(
            timesteps=timesteps, can_process_image=can_process_image, is_really_running=is_really_running
        )

    @classmethod
    def choose_high_scores_wrapper(cls, episode_name):
        try:
            assert episode_name, "episode_name is empty"

            req = ChooseHighScoresRequest.model_validate(request.get_json())
            req.name = episode_name

            resp = cls.choose_high_scores(req)
            return cls.wrap_api_response(resp)
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

        feedbackable = episode.get_feedbackable_timestep()
        if feedbackable is None:
            raise ValueError("cannot choose highscore")

        # 已反馈过的 timestep 再次打分 = 覆盖，需前端二次确认（带 overwrite=1 重试）
        if feedbackable.status == 2 and request.overwrite != 1:
            return ChooseHighScoresResponse(
                code=ErrorCode.NEED_OVERWRITE_CONFIRMATION,
                message="该 timestep 已提交过反馈，再次提交将覆盖原选择，是否继续？",
            )

        # choose

        feedbackable.chosen_highscores = request.highscores
        feedbackable.status = 2  # 1,2 => 2. restrictions of 1,2 is in episode.get_feedbackable_timestep

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

            TimestepDraftConsumptionService.start_image_processing(req.episode_name, req.timestep_draft)  # 后台线程跑图，不 join

            return cls.wrap_api_response(StartImageProcessingResponse())
        except Exception as e:
            _logger.exception("start_image_processing_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def tag_minus_last_timestep(
        cls, episode_name: str, positive_tags: str, negative_tags: str
    ) -> tuple[list[str], list[str]]:
        episode = EpisodeRepository.get_eposide(episode_name)

        last_positive_tags = []
        last_negative_tags = []

        if episode.timesteps:
            last_positive_tags, last_negative_tags = TagChecker.all_tags_in_timestep(episode.timesteps[-1])

        this_positive_tags = TagChecker.extract_all_tags(positive_tags)
        this_negative_tags = TagChecker.extract_all_tags(negative_tags)

        diff_positive = list(set(this_positive_tags) - set(last_positive_tags))
        diff_negative = list(set(this_negative_tags) - set(last_negative_tags))

        return diff_positive, diff_negative

    @classmethod
    def rollback_timestep_wrapper(cls, episode_name: str):
        try:
            assert episode_name

            req = RollbackTimestepRequest.model_validate(request.get_json())
            req.episode_name = episode_name

            assert episode_name

            resp = cls.rollback_timestep(req)

            return cls.wrap_api_response(resp)
        except Exception as e:
            _logger.exception("rollback_timestep_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def cancel_timestep_wrapper(cls, episode_name: str):
        try:
            assert episode_name

            cancel_flag_path = EpisodeRepository.episodes_dir() / episode_name / "cancel_flag"
            send_cancel(cancel_flag_path)

            return cls.wrap_api_ok({"message": "cancel signal sent"})
        except Exception as e:
            _logger.exception("cancel_timestep_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def rollback_timestep(cls, request: RollbackTimestepRequest) -> RollbackTimestepResponse:
        episode = EpisodeRepository.get_eposide(request.episode_name)

        if not episode.timesteps:
            raise ValueError("episode empty, cannot rollback")

        episode_name = request.episode_name
        assert episode_name, "episode_name is empty"

        # 跨进程防护：心跳新鲜（<1s）说明正在跑图，拒绝 rollback（前端互斥显示，后端兜底）
        if EpisodeHeartbeatService.is_really_running(episode_name):
            raise ValueError("timestep is running, cancel it first")

        rolled_i = len(episode.timesteps) - 1

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

    @classmethod
    def get_episode_list_wrapper(cls):
        try:
            req = GetEpisodeListRequest()

            resp = cls.get_episode_list(req)

            return cls.wrap_api_response(resp)
        except Exception as e:
            _logger.exception("get_episode_list_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def get_episode_list(cls, req: GetEpisodeListRequest) -> GetEpisodeListResponse:
        episode_list = EpisodeRepository.list_episodes()

        resp = GetEpisodeListResponse()

        for name, episode in episode_list:
            resp.episodes_list.append(
                EpisodeListItem(
                    name=name,
                    create_time=episode.create_time,
                )
            )

        resp.episodes_list.sort(key=lambda x: -x.create_time)

        return resp

    @classmethod
    def episode_list_page_wrapper(cls):
        return render_template("episode_list.html")

    @classmethod
    def create_episode_wrapper(cls):
        try:
            req = CreateEpisodeRequest.model_validate(request.get_json())
            resp = cls.create_episode(req)

            return cls.wrap_api_response(resp)
        except Exception as e:
            _logger.exception("create_episode_wrapper error")
            return cls.wrap_api_exception(e)  # "message": str(e)

    @classmethod
    def create_episode(cls, req: CreateEpisodeRequest) -> CreateEpisodeResponse:
        # 简单的正则校验：仅限英文、数字、下划线、连字符，长度 1-64
        if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", req.name):
            raise ValueError("Invalid name: Use only English letters, numbers, hyphens, or underscores.")

        d = EpisodeRepository.episodes_dir() / req.name
        if d.exists():
            raise ValueError("name already exist")

        # 快照机制：workflow/budget 在创建时固化进 episode.json
        workflow = req.workflow
        if not workflow:
            raise ValueError("workflow is required")
        if not Path(workflow).exists():
            raise ValueError(f"workflow not exist: {workflow}")

        episode = Episode(
            create_time=int(time.time()),
            workflow=workflow,
            invalid_tag_budget=req.invalid_tag_budget,
        )

        EpisodeRepository.save_episode(req.name, episode)

        return CreateEpisodeResponse()

    WORKFLOWS_DIR = "entropy/conf/workflows"  # 工作流发现目录（写死；没有"默认工作流"概念）

    @staticmethod
    def list_workflow_paths() -> list[str]:
        """返回全部可选工作流相对路径（= WORKFLOWS_DIR 下的所有 *.json）"""
        return sorted(p.as_posix() for p in Path(EpisodeHandler.WORKFLOWS_DIR).glob("*.json"))

    @classmethod
    def list_workflows_wrapper(cls):
        """工作流发现：WORKFLOWS_DIR 目录下的所有 *.json"""
        try:
            options = cls.list_workflow_paths()
            return jsonify({"code": 0, "message": "ok", "options": options})
        except Exception as e:
            _logger.exception("list_workflows_wrapper error")
            return cls.wrap_api_exception(e)
