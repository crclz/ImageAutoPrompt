import logging
import re
import threading
import time
import traceback
from datetime import UTC, datetime
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
from entropy.domain.models.app_config import AppConfig
from entropy.domain.models.draft import ExplorationAbstract
from entropy.domain.models.episode import Episode, EpisodeTimestep, ImagePrompt
from entropy.domain.models.error_code import ErrorCode
from entropy.domain.models.query_model import EpisodeQueryModel
from entropy.domain.services.draft_parse_service import DraftParseService
from entropy.domain.services.episode_heartbeat_service import EpisodeHeartbeatService
from entropy.domain.services.tag_checker import TagChecker
from entropy.domain.services.tag_hinting_service import TagHintingService
from entropy.infra.cancellation import FileCancellationSource, send_cancel
from entropy.infra.comfy_api import ComfyApi
from entropy.infra.comfy_health import ComfyHealth
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

            cls.start_image_processing(req)  # 后台线程跑图，不 join

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
    def image_process_guard(
        cls, request: StartImageProcessingRequest
    ) -> tuple[bool, str, ExplorationAbstract | None, list[ImagePrompt], tuple[list[str], list[str], list[str]]]:
        """
        return: do_intercept, message, prompts, (positives, negatives)
        raise: some exceptions
        """

        # base url
        current_app_config = AppConfig.read()
        base_url = current_app_config.comfyui_base_url
        assert base_url, "app config comfyui_base_url is empty"
        assert base_url.startswith("http"), "app config comfyui_base_url should start with http"

        json_file = current_app_config.workflow_api_json
        if not Path(json_file).exists():
            raise ValueError(f"not exist: {json_file}")

        # parse llm
        assert request.timestep_draft, "timestep_draft is empty"

        parse_result = DraftParseService.parse_timestep_draft(request.timestep_draft)
        if not parse_result.positives:
            raise ValueError(
                "未找到 prompt 块：draft 需要包含 ```prompt0 ... ``` 块（positive/negative 各一行），"
                '或以 ":" 开头的行（一行一个 tag）'
            )

        prompts: list[ImagePrompt] = []
        for positive, negative, lora in zip(parse_result.positives, parse_result.negatives, parse_result.loras):
            prompts.append(ImagePrompt(positive=positive, negative=negative, lora=lora))

        # parse abstract
        episode = EpisodeRepository.get_eposide(request.episode_name)
        # is_zero_index = len(episode.timesteps) == 0
        del episode

        abstract = DraftParseService.parse_exploration_abstract(request.timestep_draft)
        if not abstract and parse_result.is_friendly:
            abstract = ExplorationAbstract()
        if not abstract:
            raise ValueError("缺少 <exploration> 块")

        do_intercept = False
        message = ""

        # invalid tags interception
        invalid_tag_hint = TagHintingService.get_invalid_tag_hint(
            parse_result.positives, parse_result.negatives, current_app_config.invalid_tag_tolerance
        )
        if invalid_tag_hint:
            do_intercept = True
            message = invalid_tag_hint

        return (
            do_intercept,
            message,
            abstract,
            prompts,
            (parse_result.positives, parse_result.negatives, parse_result.loras),
        )

    @classmethod
    def create_timestep_with_draft(cls, episode_name: str, timestep_draft: str) -> int:
        """
        创建新 timestep 的公共流程（web 与 cli 共用）：
        guard（无效 tag 拦截 raise）→ comfy 健康检查 → episode 状态守卫 → append timestep + save

        return: 新 timestep 的序号 timestep_i
        raise: ValueError（拦截提示 / 状态不允许等）
        """
        request = StartImageProcessingRequest(episode_name=episode_name, timestep_draft=timestep_draft)

        current_app_config = AppConfig.read()

        do_interception, message, _, prompts, _ = cls.image_process_guard(request)
        if do_interception:
            # 拦截（如无效 tag 提示）：统一视为失败
            raise ValueError(message)

        # 任何 comfyui 访问前，先健康检查（进程内 10 分钟缓存）
        ComfyHealth.ensure_comfy_healthy(current_app_config.comfyui_base_url)

        # ======cannot perform time consuming work after here

        # check episode status
        episode = EpisodeRepository.get_eposide(episode_name)

        if not episode.can_process_image():
            raise ValueError("user should submit feedback before going on")

        # create new timestep
        timestep_i = len(episode.timesteps)

        episode.timesteps.append(EpisodeTimestep(i=timestep_i, prompts=prompts))

        EpisodeRepository.save_episode(episode_name, episode)
        del episode  # cannot reuse, because stale

        return timestep_i

    @classmethod
    def start_image_processing(
        cls,
        request: StartImageProcessingRequest,
        extra_hook=None,
        created_hook=None,
        done_hook=None,
    ) -> threading.Thread:
        """
        create new timestep, then start a daemon thread to run all images.

        return: 后台跑图线程。调用者决定是否 join（web 不 join；cli join 并处理取消）。

        created_hook: 创建 timestep 后、跑图前调用 (timestep_i)
        extra_hook: 每张图完成后调用 (image_index, image_bytes)（存图之后）
        done_hook: 跑图收尾后调用 (error: Optional[str])，None=成功，非 None=失败原因（含取消）
        """
        timestep_i = cls.create_timestep_with_draft(request.episode_name, request.timestep_draft)

        if created_hook:
            created_hook(timestep_i)

        def fn_run_many():
            cls.run_timestep_images(request.episode_name, timestep_i, extra_hook=extra_hook, done_hook=done_hook)

        run_many_thread = threading.Thread(target=fn_run_many, daemon=True)
        run_many_thread.start()

        return run_many_thread

    @classmethod
    def run_timestep_images(
        cls,
        episode_name: str,
        timestep_i: int,
        extra_hook=None,
        done_hook=None,
    ) -> None:
        """
        跑指定 timestep 的所有图片，收尾时 status 置 1（成功或失败都迁移出 running，不滞留）。
        失败（含取消）时记录 error + stacktrace 到 timestep，供 web 端展示。
        """
        current_app_config = AppConfig.read()
        template_json = Path(current_app_config.workflow_api_json).read_text("utf8")

        # 从 episode 读取该 timestep 的 prompts
        episode = EpisodeRepository.get_eposide(episode_name)
        timestep = episode.timesteps[timestep_i]
        positives = [p.positive for p in timestep.prompts]
        negatives = [p.negative for p in timestep.prompts]
        loras = [p.lora for p in timestep.prompts]
        del episode  # cannot reuse, because stale

        def complete_hook(image_index: int, image_bytes: bytes) -> None:
            # 存图（web 与 cli 共用）：save so that web page can see the picture
            pic_save_path = EpisodeRepository.pic_path(episode_name, timestep_i, image_index)
            pic_save_path.write_bytes(image_bytes)

            # 附加 hook（如 cli 打印进度）
            if extra_hook:
                extra_hook(image_index, image_bytes)

        # 跨进程取消信号源（web/cli 都可 send_cancel 写 cancel_flag）
        cancel_flag_path = EpisodeRepository.episodes_dir() / episode_name / "cancel_flag"
        cancellation_source = FileCancellationSource(cancel_flag_path)

        error: str | None = None
        stacktrace = ""

        # 心跳：with 块内持续 touch running_flag（mtime < 1s 视为在跑），退出自动停止线程并清理
        with EpisodeHeartbeatService.start_heartbeat(episode_name):
            try:
                t0 = datetime.now(UTC)
                ComfyApi.run_many(
                    current_app_config.comfyui_base_url,
                    template_json,
                    positives,
                    negatives,
                    loras,
                    complete_hook=complete_hook,
                    cancellation_source=cancellation_source,
                )

                dt = (datetime.now(UTC) - t0).total_seconds()
                _logger.info(f"run_many takes {dt:.1f} seconds")
            except Exception as e:
                error = str(e)
                stacktrace = traceback.format_exc()
                _logger.exception(f"run_many failed for episode {episode_name}, timestep {timestep_i}")

        # 收尾：重新读 episode（防 rollback 竞态），timestep 仍存在才写回
        episode = EpisodeRepository.get_eposide(episode_name)

        if timestep_i >= len(episode.timesteps):
            _logger.warning(f"timestep {timestep_i} no longer exists (rolled back), skip status write-back")
        else:
            episode.timesteps[timestep_i].status = 1
            episode.timesteps[timestep_i].error = error or ""
            episode.timesteps[timestep_i].stacktrace = stacktrace

            EpisodeRepository.save_episode(episode_name, episode)

        if done_hook:
            done_hook(error)

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

        episode = Episode(create_time=int(time.time()))

        EpisodeRepository.save_episode(req.name, episode)

        return CreateEpisodeResponse()
