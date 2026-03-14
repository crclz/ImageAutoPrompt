import re
from typing import List, Tuple


class LlmParseService:
    @staticmethod
    def parse_exploration_output(text: str) -> Tuple[List[str], List[str]]:
        # 1. 使用正则匹配所有 ```prompt{n} ... ``` 的块
        # 匹配组1: 索引数字, 匹配组2: 块内文本内容
        pattern = r"```prompt(\d+)\s+(.*?)\s+```"
        matches = re.findall(pattern, text, re.DOTALL)

        if not matches:
            return [], []

        positives = []
        negatives = []

        # 2. 检查索引是否从0开始且连续
        for i, (index_str, content) in enumerate(matches):
            actual_index = int(index_str)
            if actual_index != i:
                raise ValueError(f"Prompt index mismatch: expected {i}, got {actual_index}")

            # 3. 解析 Positive 和 Negative 部分
            # 逻辑：寻找 positive 关键字后的内容，直到遇到 negative 或结束
            # 寻找 negative 关键字后的内容，直到结束

            # 清理内容中的首尾空格
            content = content.strip()

            p_part = ""
            n_part = ""

            if "positive" in content and "negative" in content:
                parts = re.split(r"positive\s+|negative\s+", content)
                # split 之后第一个元素通常是空的（如果 positive 在开头）
                # 过滤掉空字符串并拿取对应部分
                valid_parts = [p.strip() for p in parts if p.strip()]
                if len(valid_parts) >= 2:
                    p_part = valid_parts[0]
                    n_part = valid_parts[1]

            positives.append(p_part)
            negatives.append(n_part)

        return positives, negatives
