from typing import List, Set, Tuple
from pathlib import Path
import csv
import re

from entropy.domain.models.episode import EpisodeTimestep


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

            tag = TagChecker.normalize_tag(tag)

            if tag:
                tags.append(tag)

        # 6. 去重并保持顺序
        return list(dict.fromkeys(tags))

    @staticmethod
    def normalize_tag(tag: str) -> str:
        if not tag:
            return ""

        # --- A. 预处理：剥离 SD 特有的权重语法 ---
        tag = tag.strip()

        # 1. 移除末尾的数值权重，如 ":1.5"
        tag = re.sub(r":[\d.]+$", "", tag)

        # 2. 移除所有“未被转义”的括号 ( ) [ ]
        # (?<!\\) 表示：匹配括号，但前提是它前面不能有反斜杠 \
        tag = re.sub(r"(?<!\\)[\(\)\[\]]", "", tag)

        # --- B. 归一化：转换为 Danbooru 标准格式 ---
        # 3. 转小写
        tag = tag.lower()

        # 4. 移除特定的前缀 (如 artist:, character: 等)
        prefixes = ["artist:", "character:", "copyright:", "general:"]
        for p in prefixes:
            tag = tag.removeprefix(p)

        # 5. 还原转义后的内容括号：将 \( 还原为 (
        # 注意：此时剩下的 \( 已经是标签内容的一部分了
        tag = tag.replace(r"\(", "(").replace(r"\)", ")")
        tag = tag.replace(r"\[", "[").replace(r"\]", "]")

        # 6. 空格转下划线，压缩连续下划线
        tag = tag.replace(" ", "_")
        tag = re.sub(r"_+", "_", tag)

        # 7. 最终修剪
        tag = tag.strip("_ ")

        # 下划线转空格
        tag = tag.replace("_", " ")
        return tag

    @staticmethod
    def get_not_exist_tags(s: str) -> List[str]:
        tags = TagChecker.extract_all_tags(s)

        not_exist = [p for p in tags if not TagChecker.exist_tag(p)]

        return not_exist

    @staticmethod
    def exist_tag(tag: str) -> bool:
        tag = TagChecker.normalize_tag(tag)

        return tag in TagChecker._tag_set

    @classmethod
    def all_tags_in_timestep(cls, t: EpisodeTimestep) -> Tuple[List[str], List[str]]:
        positive_tags = []
        negative_tags = []

        for prompt in t.prompts:
            positive_tags += cls.extract_all_tags(prompt.positive)
            negative_tags += cls.extract_all_tags(prompt.negative)

        positive_tags = list(set(positive_tags))
        negative_tags = list(set(negative_tags))

        return positive_tags, negative_tags


TagChecker.init_tag_set()
