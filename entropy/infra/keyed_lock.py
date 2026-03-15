import threading
from contextlib import contextmanager
from typing import Dict


class KeyedLock:
    def __init__(self):
        self.locks: Dict[str, threading.Lock] = {}
        self.main_lock = threading.Lock()

    def _get_or_create_lock(self, key: str) -> threading.Lock:
        """内部方法：确保获取 Key 对应的锁对象是线程安全的"""
        with self.main_lock:
            if key not in self.locks:
                self.locks[key] = threading.Lock()
            return self.locks[key]

    @contextmanager
    def lock(self, key: str, timeout: float = -1):
        a_lock = self._get_or_create_lock(key)

        # 锁定特定资源
        a_lock.acquire(timeout=timeout)
        try:
            yield
        finally:
            a_lock.release()

    def is_locked(self, key: str) -> bool:
        a_lock = self._get_or_create_lock(key)

        return a_lock.locked()
