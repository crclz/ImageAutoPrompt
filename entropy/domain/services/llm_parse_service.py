import json
import re
from typing import List, Optional, Tuple

import pydantic


class ExplorationAbstract(pydantic.BaseModel):
    type: str = ""
    description: str = ""
    keywords: List[str] = []


class LlmParseService:
    @staticmethod
    def parse_exploration_output(text: str) -> Tuple[List[str], List[str], List[str], bool]:
        """
        return: positives, negatives, loras, is_user_friendly_format_input
        """
        success, positives, negatives = LlmParseService.try_parse_user_friendly(text)
        if success:
            loras = [""] * len(positives)
            return positives, negatives, loras, True

        del success, positives, negatives

        # 1. 使用正则匹配所有 ```prompt{n} ... ``` 的块
        # 匹配组1: 索引数字, 匹配组2: 块内文本内容
        pattern = r"```prompt(\d+)\s+(.*?)\s+```"
        matches = re.findall(pattern, text, re.DOTALL)

        if not matches:
            return [], [], [], False

        positives = []
        negatives = []
        loras = []

        # 2. 检查索引是否从0开始且连续
        for i, (index_str, content) in enumerate(matches):
            actual_index = int(index_str)
            if actual_index != i:
                raise ValueError(f"Prompt index mismatch: expected {i}, got {actual_index}")

            # 3. 解析 Positive、Negative、Lora 部分
            # 逻辑：寻找 positive 关键字后的内容，直到遇到 negative / lora 或结束
            # lora 部分可选：没有 lora 关键字时 lora 为空字符串

            # 清理内容中的首尾空格
            content = content.strip()

            p_part = ""
            n_part = ""
            l_part = ""

            if not ("positive" in content and "negative" in content):
                raise ValueError(f"positive and negative not found. prompt_{i}")

            parts = re.split(r"positive\s+|negative\s+|lora\s+", content)
            # split 之后第一个元素通常是空的（如果 positive 在开头）
            # 过滤掉空字符串并拿取对应部分
            valid_parts = [p.strip() for p in parts if p.strip()]
            if len(valid_parts) >= 2:
                p_part = valid_parts[0]
                n_part = valid_parts[1]
                if len(valid_parts) >= 3:
                    l_part = valid_parts[2]
            else:
                raise ValueError(f"format error prompt_{i}")

            if n_part.strip().lower() == "null":
                n_part = ""

            if l_part.strip().lower() == "null":
                l_part = ""

            positives.append(p_part)
            negatives.append(n_part)
            loras.append(l_part)

        return positives, negatives, loras, False

    @staticmethod
    def try_parse_user_friendly(s: str) -> Tuple[bool, List[str], List[str]]:
        """every line start with semicolon"""

        lines = s.splitlines()
        lines = [p.strip() for p in lines]
        lines = [p for p in lines if p]

        positives = []

        for line in lines:
            if not line.startswith(":"):
                return False, [], []

            positives.append(line.removeprefix(":").strip())

        negatives = [""] * len(positives)

        return True, positives, negatives

    @staticmethod
    def parse_danbooru_search(text: str) -> List[str]:
        # 1. Use regex to find the content inside the ```danbooru_search block
        # re.DOTALL allows the '.' to match newlines
        pattern = r"```danbooru_search\s+(.*?)\s+```"
        match = re.search(pattern, text, re.DOTALL)

        if not match:
            return []

        # 2. Extract the captured group and parse as JSON
        json_content = match.group(1)
        data = json.loads(json_content)

        # 3. Return the "query_list" field
        return data.get("query_list", [])

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
