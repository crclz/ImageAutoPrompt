import json
import re
from typing import Optional, Tuple

import pydantic

from entropy.domain.models.draft import ExplorationAbstract, TimestepDraftParseResult


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
    def parse_prompt_block(content: str, index: int) -> Tuple[str, str, str]:
        """按行解析一个 prompt 块的 positive/negative/lora 段（顺序不限），返回 (positive, negative, lora)。"""

        sections = {"positive": [], "negative": [], "lora": []}
        current: Optional[str] = None

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
    def try_parse_user_friendly(s: str) -> Optional[TimestepDraftParseResult]:
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
    def parse_exploration_abstract(text: str) -> Optional[ExplorationAbstract]:
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
