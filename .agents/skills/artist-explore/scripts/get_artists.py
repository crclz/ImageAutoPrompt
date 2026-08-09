"""从 artist 库中随机抽样，输出完整的 artist 块。

用法（本脚本依赖当前工作目录，需在仓库根目录执行）：
    uv run .agents/skills/artist-explore/scripts/get_artists.py --dropout=0.3

--dropout 必传，取值 [0, 1)：随机丢弃对应比例的 artist 块。
输出的每个块为 "## artist:xxx" 标题 + 画风描述（保留原始 // 注释）。
本脚本是 artist 库的唯一出口，调用方不要直接阅读 library/artists.md。
"""

import argparse
import random
import sys
from pathlib import Path


def parse_artist_blocks(text: str) -> list[str]:
    """将 artists.md 解析为完整的 artist 块（标题 + 描述），按原顺序返回。"""
    blocks: list[str] = []
    cur: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## artist:"):
            if cur is not None:
                blocks.append("\n".join(cur))
            cur = [line]
        elif cur is not None and line.strip():
            cur.append(line.strip())
    if cur is not None:
        blocks.append("\n".join(cur))
    return blocks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从 artist 库按 dropout 比例随机抽样，输出完整 artist 块"
    )
    parser.add_argument("--dropout", type=float, required=True,
                        help="随机丢弃比例，必传，取值 [0, 1)")
    args = parser.parse_args()

    if not 0 <= args.dropout < 1:
        parser.error(f"--dropout 必须在 [0, 1) 区间内，收到: {args.dropout}")

    artists_file = Path("library/artists.md")
    if not artists_file.is_file():
        sys.exit("找不到 library/artists.md，请在仓库根目录运行本脚本")
    blocks = parse_artist_blocks(artists_file.read_text(encoding="utf-8"))

    random.shuffle(blocks)
    remaining = [b for b in blocks if random.random() >= args.dropout]
    dropped = [b for b in blocks if b not in remaining]

    print(f"Total artists: {len(blocks)}")
    print(f"Dropout: {args.dropout:.2f}")
    print(f"Remaining: {len(remaining)}")
    print(f"Dropped: {len(dropped)}")
    print()

    print("=== REMAINING ARTISTS ===")
    for b in remaining:
        print()
        print(b)


if __name__ == "__main__":
    sys.exit(main())
