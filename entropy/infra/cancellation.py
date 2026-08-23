from pathlib import Path


class FileCancellationSource:
    """基于文件系统的跨进程取消信号源。

    取消者调用 send_cancel(path) 创建信号文件；本类检测到文件存在即视为取消，
    并消费掉该文件（删除 + 缓存状态），后续 should_cancel() 恒返回 True。
    """

    def __init__(self, path, clean_existing: bool = True):
        self.path = Path(path)
        self.cancelled = False

        if clean_existing:
            self.path.unlink(missing_ok=True)

    def should_cancel(self) -> bool:
        if self.cancelled:
            return True

        if self.path.exists():
            self.cancelled = True
            self.path.unlink(missing_ok=True)

        return self.cancelled


def send_cancel(path) -> None:
    """创建取消信号文件（幂等：已存在则跳过）。"""
    Path(path).touch(exist_ok=True)
