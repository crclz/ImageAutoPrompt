import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from entropy.infra.episode_repository import EpisodeRepository


class EpisodeHeartbeatService:
    """跨进程跑图心跳：running_flag 文件 mtime 距今 < 1s 视为正在跑图（CLI/web 同判定）。"""

    _RUNNING_FLAG = "running_flag"
    _HEARTBEAT_INTERVAL = 0.3  # 续约 touch 周期（秒）
    _RUNNING_THRESHOLD_SECONDS = 1.0  # mtime 距今 < 该值视为在跑（秒）

    @classmethod
    def flag_path(cls, episode_name: str) -> Path:
        return EpisodeRepository.episodes_dir() / episode_name / cls._RUNNING_FLAG

    @classmethod
    def is_really_running(cls, episode_name: str) -> bool:
        """心跳新鲜（存在且 mtime 距今 < 1s）视为正在跑图。"""
        flag = cls.flag_path(episode_name)
        if not flag.exists():
            return False
        return (time.time() - flag.stat().st_mtime) < cls._RUNNING_THRESHOLD_SECONDS

    @classmethod
    def touch(cls, episode_name: str) -> None:
        flag = cls.flag_path(episode_name)
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()

    @classmethod
    def clear(cls, episode_name: str) -> None:
        cls.flag_path(episode_name).unlink(missing_ok=True)

    @classmethod
    @contextmanager
    def start_heartbeat(cls, episode_name: str) -> Generator[None, None, None]:
        """
        with 块内持续 touch 心跳；退出时停止线程并删除 flag（任何退出路径都执行）。

        进入时先同步 touch 一次，保证 with 块一开始心跳即新鲜。
        """
        flag = cls.flag_path(episode_name)
        cls.touch(episode_name)

        stop = threading.Event()

        def _beat() -> None:
            while not stop.is_set():
                flag.touch()
                time.sleep(cls._HEARTBEAT_INTERVAL)

        hb_thread = threading.Thread(target=_beat, daemon=True)
        hb_thread.start()

        try:
            yield
        finally:
            stop.set()
            hb_thread.join(timeout=1)
            flag.unlink(missing_ok=True)
