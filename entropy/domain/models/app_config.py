from pathlib import Path
import time

import pydantic
import functools
import yaml


class AppConfig(pydantic.BaseModel):
    comfyui_base_url: str
    workflow_api_json: str
    workflow_timeout_seconds: int
    prompt_file: str

    invalid_tag_tolerance: int

    extra_valid_tag_file: str = ""
    rag_for_exploration_keyword: int

    @staticmethod
    @functools.lru_cache(5)
    def _read(window_id: int) -> "AppConfig":
        s = Path("app_config.yaml").read_text("utf8")
        obj = yaml.safe_load(s)

        return AppConfig.model_validate(obj)

    @staticmethod
    def read() -> "AppConfig":
        window_size = 200  # 200ms
        window_id = int(time.time() * 1000) // window_size

        return AppConfig._read(window_id)
