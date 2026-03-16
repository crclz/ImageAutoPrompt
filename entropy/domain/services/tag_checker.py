from typing import List, Set
from pathlib import Path
import csv
import re


class TagChecker:
    _tag_set: Set[str] = set()

    @staticmethod
    def init_tag_set():
        lines = Path("datasets/danbooru-10w.txt").read_text("utf8").splitlines()
        reader = csv.reader(lines)

        rows: List[dict] = []

        for i, item in enumerate(reader):
            original = item[0]
            count = item[1]

            normalized = TagChecker.normalize_tag(original)

            TagChecker._tag_set.add(normalized)

        # extra tags
        extra_tag_string = """
        masterpiece, best quality,newest,absurdres,
        worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands
        """
        extra_tags = TagChecker.extract_all_tags(extra_tag_string)

        for extra_tag in extra_tags:
            TagChecker._tag_set.add(extra_tag)

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
    def normalize_tag(tag: str) -> str:
        r"""
        将标签归一化为 Danbooru 标准存储格式：
        1. 转小写
        2. 还原转义字符 ( \( -> ( )
        3. 空格转下划线 ( long hair -> long_hair )
        4. 压缩并修剪多余的下划线和空白
        """
        if not tag:
            return ""

        # 1. 转小写 (Danbooru 标签库不区分大小写)
        tag = tag.lower()

        tag = tag.removeprefix("artist:")

        # 2. 处理转义符：将 \( 和 \) 还原成普通的 ( 和 )
        # 这样 'bb \(baalbuddy\)' 和 'bb (baalbuddy)' 就能匹配上
        tag = tag.replace(r"\(", "(").replace(r"\)", ")")
        tag = tag.replace(r"\[", "[").replace(r"\]", "]")

        # 3. 将空格替换为下划线
        tag = tag.replace(" ", "_")

        # 4. 压缩连续的下划线 (例如 'reading   book' -> 'reading___book' -> 'reading_book')
        tag = re.sub(r"_+", "_", tag)

        # 5. 去除首尾的空格和下划线
        return tag.strip("_ ")

    @staticmethod
    def get_not_exist_tags(s: str) -> List[str]:
        tags = TagChecker.extract_all_tags(s)

        tags = [TagChecker.normalize_tag(p) for p in tags]

        not_exist = [p for p in tags if p not in TagChecker._tag_set]

        return not_exist


TagChecker.init_tag_set()
