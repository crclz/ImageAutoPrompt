import logging
import threading
import traceback
from datetime import UTC, datetime
from pathlib import Path

from entropy.domain.models.app_config import AppConfig
from entropy.domain.models.episode import EpisodeTimestep
from entropy.domain.services.draft_parse_service import DraftParseService
from entropy.domain.services.episode_heartbeat_service import EpisodeHeartbeatService
from entropy.infra.cancellation import FileCancellationSource
from entropy.infra.comfy_api import ComfyApi
from entropy.infra.comfy_health import ComfyHealth
from entropy.infra.episode_repository import EpisodeRepository

_logger = logging.getLogger(__name__)


class TimestepDraftConsumptionService:
    """timestep draft 的消费与运行生命周期管理：guard → 创建 timestep → 后台线程跑图。"""

    @classmethod
    def create_timestep_with_draft(cls, episode_name: str, timestep_draft: str) -> int:
        """
        创建新 timestep 的公共流程（web 与 cli 共用）：
        guard（无效 tag 拦截 raise）→ comfy 健康检查 → episode 状态守卫 → append timestep + save

        return: 新 timestep 的序号 timestep_i
        raise: ValueError（拦截提示 / 状态不允许等）
        """
        current_app_config = AppConfig.read()

        do_interception, message, prompts = DraftParseService.image_process_guard(timestep_draft)
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
        episode_name: str,
        timestep_draft: str,
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
        timestep_i = cls.create_timestep_with_draft(episode_name, timestep_draft)

        if created_hook:
            created_hook(timestep_i)

        def fn_run_many():
            cls.run_timestep_images(episode_name, timestep_i, extra_hook=extra_hook, done_hook=done_hook)

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
