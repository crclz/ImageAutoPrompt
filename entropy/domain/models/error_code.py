from enum import IntEnum


class ErrorCode(IntEnum):
    """特殊错误码：仅当前端需要做逻辑分支时使用，从 601899001 开始递增。"""

    NEED_OVERWRITE_CONFIRMATION = 601899001  # 已反馈的 timestep 再次打分：前端二次确认后带 overwrite=1 重试
