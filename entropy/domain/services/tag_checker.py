from typing import List

import re


class TagChecker:
    @staticmethod
    def extract_all_tags(prompt: str) -> list[str]:
        if not prompt:
            return []

        # 1. 预处理：去掉换行符，将多余空白压缩
        prompt = prompt.replace("\n", " ").strip()

        # 2. 移除 LoRA, Hypernetwork 等辅助语法 (例如 <lora:name:1>)
        # 这些通常不属于 Danbooru 标签库，不需要 check
        prompt = re.sub(r"<[^>]+>", " ", prompt)

        # 3. 按逗号分割
        raw_chunks = prompt.split(",")

        tags = []
        for chunk in raw_chunks:
            tag = chunk.strip()
            if not tag:
                continue

            # 4. 递归剥离权重的括号 () 和 []
            # 注意：这里只剥离“成对包裹”在最外层的括号
            while True:
                # 匹配 (tag:1.2) 或 (tag)
                # 使用正则处理以确保不误删中间的转义括号
                # 匹配模式：开头是 ( 或 [，结尾是 ) 或 ]，或者是 :数字 结尾

                # 处理末尾的权重数值，如 :1.5
                tag = re.sub(r":[\d.]+\s*$", "", tag).strip()

                # 剥离成对的括号
                if (tag.startswith("(") and tag.endswith(")")) or (tag.startswith("[") and tag.endswith("]")):
                    tag = tag[1:-1].strip()
                else:
                    break

            # 5. 处理转义字符与格式转换
            # Danbooru 官方标签使用下划线，Prompt 中常使用空格
            # 移除转义斜杠 \( -> (
            tag = tag.replace(r"\(", "(").replace(r"\)", ")")
            tag = tag.replace(r"\[", "[").replace(r"\]", "]")

            # 将空格转换为下划线（这是 Danbooru 数据库的标准存储格式）
            tag = tag.replace(" ", "_")

            # 再次清理多余下划线（处理 "reading a  book" 这种多空格情况）
            tag = re.sub(r"_+", "_", tag).strip("_")

            if tag:
                tags.append(tag)

        # 6. 去重并保持顺序
        return list(dict.fromkeys(tags))

    @staticmethod
    def get_not_exist_tags(s: str) -> List[str]: ...
