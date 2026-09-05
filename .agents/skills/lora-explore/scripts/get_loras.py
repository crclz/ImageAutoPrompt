"""从 lora 库（library/{arch}_loras.yaml）过滤 + 随机抽样，输出 <lora:xxx> 引用行。

用法（本脚本依赖当前工作目录，需在仓库根目录执行）：
    python .agents/skills/lora-explore/scripts/get_loras.py --arch=anima --limit=5
    python .agents/skills/lora-explore/scripts/get_loras.py --arch=noob --limit=16

--arch 必传，noob / anima 二选一，决定读取 library/noob_loras.yaml 还是 library/anima_loras.yaml。
--limit 必传，取值 >= 1：过滤 + shuffle 后取前 N 个。
过滤规则（对每条 lora 的 my_comment strip 后严格匹配行首记号，笨办法硬编码，不用正则）：
    - 行首记号必须是 <1> <3> <3+> <3-> <5> <5-> 之一，否则视为未评分/格式有误：
      不采用，并在 stderr 用英文警告列出（顺带告知用户，提醒其补评分）
    - 记号为 <1>（不采用）或 <3->（质量可能有小问题）的剔除
    - 记号为 <未评>（已知未评估，如孤儿条目）：静默剔除，不警告
stdout 只输出结果列表（一行一个 <lora:xxx>），诊断信息一律走 stderr。
本脚本是 noob / anima lora 库的唯一出口，调用方不要直接阅读 library/*_loras.yaml。
"""

import argparse
import random
import sys
from pathlib import Path

import yaml

VALID_RATINGS = ("1", "3", "3+", "3-", "5", "5-")
EXCLUDED_RATINGS = ("1", "3-")
UNRATED_TOKEN = "未评"


def parse_rating(my_comment) -> str | None:
    """严格匹配 my_comment 行首的评分记号，返回记号内容（如 "5-"）；无有效记号返回 None。"""
    if not isinstance(my_comment, str):
        return None
    comment = my_comment.strip()
    for rating in (*VALID_RATINGS, UNRATED_TOKEN):
        if comment.startswith(f"<{rating}>"):
            return rating
    return None


def build_pool(loras: dict) -> tuple[list[str], list[str]]:
    """返回（可用 lora 名列表, 未评分/格式有误的 lora 名列表）。

    <未评> 属于已知状态，静默剔除，不进警告列表。
    """
    pool: list[str] = []
    unrated: list[str] = []
    for name, entry in loras.items():
        rating = parse_rating((entry or {}).get("my_comment"))
        if rating == UNRATED_TOKEN:
            continue
        if rating is None:
            unrated.append(name)
        elif rating not in EXCLUDED_RATINGS:
            pool.append(name)
    return pool, unrated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从 lora 库过滤 + 随机抽样，输出 <lora:xxx> 一行一个"
    )
    parser.add_argument("--arch", required=True, choices=("noob", "anima"),
                        help="模型线，必传：noob 读 library/noob_loras.yaml，anima 读 library/anima_loras.yaml")
    parser.add_argument("--limit", type=int, required=True,
                        help="抽样数量，必传，取值 >= 1")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error(f"--limit 必须 >= 1，收到: {args.limit}")

    loras_file = Path(f"library/{args.arch}_loras.yaml")
    if not loras_file.is_file():
        sys.exit(f"找不到 {loras_file}，请在仓库根目录运行本脚本")

    data = yaml.safe_load(loras_file.read_text(encoding="utf-8"))
    loras = (data or {}).get("loras") or {}

    pool, unrated = build_pool(loras)

    if unrated:
        print(
            f"Found {len(unrated)} unrated or invalid-rating loras, "
            "which will NOT be used. Please rate them later: " + ", ".join(unrated),
            file=sys.stderr,
        )

    random.shuffle(pool)
    for name in pool[: args.limit]:
        print(f"<lora:{name}>")


if __name__ == "__main__":
    sys.exit(main())
