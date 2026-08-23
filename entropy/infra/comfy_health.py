"""
ComfyUI 健康检查（进程内缓存）。

任何 comfyui 访问前调用 ensure_comfy_healthy(base_url)：
- 探测 GET {base_url}/system_stats（参考 batch_v2_job.py 的 _check_health）
- 进程内缓存：探测成功的结果 10 分钟内不重复探测
- 探测失败不缓存，下次调用立即重试（服务恢复后能马上重新探测）
"""

import logging
import threading
import time

import requests

_logger = logging.getLogger(__name__)

HEALTH_TIMEOUT_SECONDS = 2
HEALTH_CACHE_TTL_SECONDS = 10 * 60  # 10 分钟

_lock = threading.Lock()
_healthy_cache: dict[str, float] = {}  # base_url -> 上次探测成功的时间戳


class ComfyHealth:
    @staticmethod
    def ensure_comfy_healthy(base_url: str) -> None:
        """
        探测 ComfyUI 是否可达。失败抛出 ValueError（带清晰错误消息）。

        raise: ValueError
        """
        base_url = base_url.removesuffix("/")

        now = time.time()
        with _lock:
            checked_at = _healthy_cache.get(base_url)
            if checked_at is not None and now - checked_at < HEALTH_CACHE_TTL_SECONDS:
                return

        try:
            resp = requests.get(f"{base_url}/system_stats", timeout=HEALTH_TIMEOUT_SECONDS)
            if resp.ok:
                with _lock:
                    _healthy_cache[base_url] = time.time()
                _logger.info(f"comfyui health check passed: {base_url}")
                return
            err = f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            err = str(e)

        raise ValueError(
            f"无法连接到 ComfyUI 服务 {base_url}（{err}），请确认服务已启动且端口正确。"
        )
