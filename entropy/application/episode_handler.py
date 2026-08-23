from datetime import datetime
import logging
from pathlib import Path
import re
from threading import Thread
import time
from typing import List, Optional, Tuple


from entropy.domain.models.app_config import AppConfig
from entropy.domain.models.episode import Episode, EpisodeTimestep, ImagePrompt
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
from entropy.domain.models.query_model import (
    EpisodeQueryModel,
    TimestepQueryModel,
)
from entropy.domain.models.draft import ExplorationAbstract
from entropy.domain.services.draft_parse_service import DraftParseService
from entropy.domain.services.tag_checker import TagChecker
from entropy.domain.services.tag_hinting_service import TagHintingService
from entropy.infra.comfy_api import ComfyApi
from entropy.infra.comfy_health import ComfyHealth
from entropy.infra.episode_repository import EpisodeRepository
from flask import jsonify, make_response, render_template, request

from entropy.infra.keyed_lock import KeyedLock

_logger = logging.getLogger(__name__)

_episode_timestep_lock = KeyedLock()


class EpisodeHandler:
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
            "code": -1,  # -1 = 未分类错误
            "message": str(e),
            # "stack": traceback.format_exc(),
        }

        return make_response(jsonify(err_data), 400)

    @staticmethod
    def wrap_api_ok(data: Optional[dict] = None) -> dict:
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
    def format_observation(cls, timesteps: List[TimestepQueryModel]) -> None:
        for i, timestep in enumerate(timesteps):
            assert i == timestep.i

            if timestep.status == 2:
                ob = "System:"

                ob += f" 下列是用户对 timestep={i} 的评价:\n"

                ob += "用户: NewHighScore: "
                if timestep.chosen_highscores:
                    for highscore in timestep.chosen_highscores:
                        llm_info = highscore.format_llm()
                        ob += f"{llm_info}, "
                else:
                    ob += "NO"

                ob += "\n"

                if i == len(timesteps) - 1:
                    ob += f"System: 接下来请给出timestep={len(timesteps)}的探索"
                ob += "\n"

                timestep.observation = ob

    @classmethod
    def get_episode_data(cls, name: str) -> EpisodeQueryModel:
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel
        """

        episode = EpisodeRepository.get_eposide(name)
        timesteps = EpisodeRepository.get_timesteps_query_model(name)

        # format observation
        cls.format_observation(timesteps)

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

            resp = cls.start_image_processing(req)

            return cls.wrap_api_response(resp)
        except Exception as e:
            _logger.exception("start_image_processing_wrapper error")
            return cls.wrap_api_exception(e)

    @classmethod
    def tag_minus_last_timestep(
        cls, episode_name: str, positive_tags: str, negative_tags: str
    ) -> Tuple[List[str], List[str]]:
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
    ) -> Tuple[bool, str, Optional[ExplorationAbstract], List[ImagePrompt], Tuple[List[str], List[str], List[str]]]:
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
                "或以 \":\" 开头的行（一行一个 tag）"
            )

        prompts: List[ImagePrompt] = []
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
            raise ValueError(
                "缺少 <exploration> 块：请在文件头部用 <exploration>{\"type\":...,\"description\":...,\"keywords\":[...]}</exploration>"
                " 描述探索方向（type 为 artist_only / lora_only / free）"
            )

        do_intercept = False
        message = ""

        # invalid tags interception
        invalid_tag_hint = TagHintingService.get_invalid_tag_hint(parse_result.positives, parse_result.negatives)
        if invalid_tag_hint:
            do_intercept = True
            message = invalid_tag_hint

        return do_intercept, message, abstract, prompts, (parse_result.positives, parse_result.negatives, parse_result.loras)

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

        do_interception, message, _abstract, prompts, (positives, negatives, loras) = cls.image_process_guard(request)
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
        join=False,
        extra_hook=None,
        created_hook=None,
    ) -> StartImageProcessingResponse:
        """
        create new timestep. when done, change status from 0 to 1
        change EpisodeTimestep.status from 0 to 1.

        created_hook: 创建 timestep 后、跑图前调用 (timestep_i)
        extra_hook: 每张图完成后调用 (image_index, image_bytes)（存图之后）
        """
        timestep_i = cls.create_timestep_with_draft(request.episode_name, request.timestep_draft)

        if created_hook:
            created_hook(timestep_i)

        def fn_run_many():
            cls.run_timestep_images(request.episode_name, timestep_i, extra_hook=extra_hook)

        run_many_thread = Thread(target=fn_run_many, daemon=True)
        run_many_thread.start()

        if join:
            run_many_thread.join()

        return StartImageProcessingResponse()

    @classmethod
    def run_timestep_images(
        cls,
        episode_name: str,
        timestep_i: int,
        extra_hook=None,
    ) -> None:
        """
        跑指定 timestep 的所有图片（锁内 run_many），全部完成后 status 置 1。
        每张图完成时默认存图到 images/；extra_hook 在存图后追加调用 (image_index, image_bytes)
        """
        key = f"{episode_name}:{timestep_i}"

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

        with _episode_timestep_lock.lock(key, 0.5):
            t0 = datetime.now()
            ComfyApi.run_many(
                current_app_config.comfyui_base_url,
                template_json,
                positives,
                negatives,
                loras,
                complete_hook=complete_hook,
            )

            dt = (datetime.now() - t0).total_seconds()
            _logger.info(f"run_many takes {dt:.1f} seconds")

            episode = EpisodeRepository.get_eposide(episode_name)
            episode.timesteps[timestep_i].status = 1

            EpisodeRepository.save_episode(episode_name, episode)

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
