import json
import re
from pathlib import Path

import pydantic

from entropy.domain.models.app_config import AppConfig
from entropy.domain.models.draft import ExplorationAbstract, TimestepDraftParseResult
from entropy.domain.models.episode import ImagePrompt
from entropy.domain.services.tag_hinting_service import TagHintingService


class DraftParseService:
    @staticmethod
    def parse_timestep_draft(text: str) -> TimestepDraftParseResult:
        """
        解析 timestep draft 文本。
        支持两种格式：
        1. 用户手工输入：每行以 ':' 开头（is_friendly=True）
        2. LLM 输出：多个 ```prompt{n} ... ``` 块（is_friendly=False）
        """
        friendly_result = DraftParseService.try_parse_user_friendly(text)
        if friendly_result is not None:
            return friendly_result

        # 匹配所有 ```prompt{n} ... ``` 块
        pattern = r"```prompt(\d+)\s+(.*?)\s+```"
        matches = re.findall(pattern, text, re.DOTALL)

        if not matches:
            return TimestepDraftParseResult()

        positives = []
        negatives = []
        loras = []

        # 索引必须从 0 开始且连续
        for i, (index_str, content) in enumerate(matches):
            actual_index = int(index_str)
            if actual_index != i:
                raise ValueError(f"prompt 索引不连续：期望 {i}，实际 {actual_index}")

            positive, negative, lora = DraftParseService.parse_prompt_block(content, i)
            positives.append(positive)
            negatives.append(negative)
            loras.append(lora)

        return TimestepDraftParseResult(positives=positives, negatives=negatives, loras=loras, is_friendly=False)

    @staticmethod
    def parse_prompt_block(content: str, index: int) -> tuple[str, str, str]:
        """按行解析一个 prompt 块的 positive/negative/lora 段（顺序不限），返回 (positive, negative, lora)。"""

        sections = {"positive": [], "negative": [], "lora": []}
        current: str | None = None

        for line in content.splitlines():
            stripped = line.strip()
            keyword = stripped.lower()

            if keyword in sections:
                current = keyword
            elif current and stripped:
                sections[current].append(stripped)

        positive = "\n".join(sections["positive"])
        negative = "\n".join(sections["negative"])
        lora = "\n".join(sections["lora"])

        if not positive or not negative:
            raise ValueError(f"prompt_{index} 缺少 positive 或 negative 段")

        if negative.lower() == "null":
            negative = ""

        if lora.lower() == "null":
            lora = ""

        return positive, negative, lora

    @staticmethod
    def try_parse_user_friendly(s: str) -> TimestepDraftParseResult | None:
        """每行以 ':' 开头的手工输入格式；不是该格式（或输入为空）时返回 None"""

        lines = s.splitlines()
        lines = [p.strip() for p in lines]
        lines = [p for p in lines if p]

        if not lines:
            return None

        positives = []

        for line in lines:
            if not line.startswith(":"):
                return None

            positives.append(line.removeprefix(":").strip())

        negatives = [""] * len(positives)
        loras = [""] * len(positives)

        return TimestepDraftParseResult(positives=positives, negatives=negatives, loras=loras, is_friendly=True)

    @staticmethod
    def parse_exploration_abstract(text: str) -> ExplorationAbstract | None:
        """
        兼容三种形态:
        1. <exploration>```exploration {json}```</exploration> (旧 draft)
        2. <exploration> {json} </exploration> (新 draft)
        3. ```exploration {json}``` (LLM 直接回复的裸围栏)

        raise: ValueError, JSON 非法时给中文指导式报错
        """
        json_content = None

        # 1. 先找 <exploration> 标签包裹的内容（围栏可选）
        match = re.search(r"<exploration>\s*(?:```exploration\s*)?(.*?)(?:\s*```)?\s*</exploration>", text, re.DOTALL)
        if match:
            json_content = match.group(1)
        else:
            # 2. 兜底：裸 ```exploration 围栏
            match = re.search(r"```exploration\s+(.*?)\s+```", text, re.DOTALL)
            if match:
                json_content = match.group(1)

        if not json_content:
            return None

        try:
            obj = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"<exploration> 内容不是合法 JSON：{e}")

        try:
            return ExplorationAbstract.model_validate(obj)
        except pydantic.ValidationError as e:
            raise ValueError(f"<exploration> 字段校验失败：{e}")

    @classmethod
    def image_process_guard(
        cls, timestep_draft: str, workflow: str | None = None, invalid_tag_budget: int | None = None
    ) -> tuple[bool, str, list[ImagePrompt]]:
        """
        校验并解析 timestep draft，返回 (do_intercept, message, prompts)。

        workflow / invalid_tag_budget 优先取 episode 快照（None 时回退 app_config）。
        校验内容：配置（comfyui_base_url / workflow）、prompt 块、<exploration> 块、无效 tag 拦截。
        <exploration> 解析结果仅用于校验（缺块则 raise），不外传。

        raise: ValueError（配置缺失 / 缺 prompt 块 / 缺 exploration 块）
        """
        # base url
        current_app_config = AppConfig.read()
        base_url = current_app_config.comfyui_base_url
        assert base_url, "app config comfyui_base_url is empty"
        assert base_url.startswith("http"), "app config comfyui_base_url should start with http"

        json_file = workflow or current_app_config.workflow_api_json
        if not Path(json_file).exists():
            raise ValueError(f"not exist: {json_file}")

        # parse llm
        assert timestep_draft, "timestep_draft is empty"

        parse_result = cls.parse_timestep_draft(timestep_draft)
        if not parse_result.positives:
            raise ValueError(
                "未找到 prompt 块：draft 需要包含 ```prompt0 ... ``` 块（positive/negative 各一行），"
                '或以 ":" 开头的行（一行一个 tag）'
            )

        prompts: list[ImagePrompt] = []
        for positive, negative, lora in zip(parse_result.positives, parse_result.negatives, parse_result.loras):
            prompts.append(ImagePrompt(positive=positive, negative=negative, lora=lora))

        # parse abstract（仅校验缺块，结果不外传）
        abstract = cls.parse_exploration_abstract(timestep_draft)
        if not abstract and parse_result.is_friendly:
            abstract = ExplorationAbstract()
        if not abstract:
            raise ValueError("缺少 <exploration> 块")

        do_intercept = False
        message = ""

        # invalid tags interception
        budget = invalid_tag_budget if invalid_tag_budget is not None else current_app_config.invalid_tag_tolerance
        invalid_tag_hint = TagHintingService.get_invalid_tag_hint(parse_result.positives, parse_result.negatives, budget)
        if invalid_tag_hint:
            do_intercept = True
            message = invalid_tag_hint

        return do_intercept, message, prompts
