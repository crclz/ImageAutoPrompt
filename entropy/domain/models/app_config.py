import functools
import time
from pathlib import Path

import pydantic
import yaml


class AppConfig(pydantic.BaseModel):
    comfyui_base_url: str
    workflow_api_json: str
    workflow_timeout_seconds: int

    invalid_tag_tolerance: int

    extra_valid_tag_file: str = ""

    port: int = 5000

    @staticmethod
    @functools.lru_cache(5)
    def _read(window_id: int) -> "AppConfig":
        s = Path("entropy/conf/app_config.yaml").read_text("utf8")
        obj = yaml.safe_load(s)

        return AppConfig.model_validate(obj)

    @staticmethod
    def read() -> "AppConfig":
        window_size = 200  # 200ms
        window_id = int(time.time() * 1000) // window_size

        return AppConfig._read(window_id)
