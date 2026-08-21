"""从 lora 库中随机抽样，输出完整的 lora 块。

用法（本脚本依赖当前工作目录，需在仓库根目录执行）：
    uv run .agents/skills/lora-explore/scripts/get_loras.py --dropout=0.3

--dropout 必传，取值 [0, 1)：随机丢弃对应比例的 lora 块。
输出的每个块为 "## <lora:xxx>" 标题 + 描述（保留原始 // 注释）。
本脚本是 lora 库的唯一出口，调用方不要直接阅读 library/noob_loras.md。
"""

import argparse
import random
import sys
from pathlib import Path


def parse_lora_blocks(text: str) -> list[str]:
    """将 noob_loras.md 解析为完整的 lora 块（标题 + 描述），按原顺序返回。"""
    blocks: list[str] = []
    cur: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## <lora:"):
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
        description="从 lora 库按 dropout 比例随机抽样，输出完整 lora 块"
    )
    parser.add_argument("--dropout", type=float, required=True,
                        help="随机丢弃比例，必传，取值 [0, 1)")
    args = parser.parse_args()

    if not 0 <= args.dropout < 1:
        parser.error(f"--dropout 必须在 [0, 1) 区间内，收到: {args.dropout}")

    loras_file = Path("library/noob_loras.md")
    if not loras_file.is_file():
        sys.exit("找不到 library/noob_loras.md，请在仓库根目录运行本脚本")
    blocks = parse_lora_blocks(loras_file.read_text(encoding="utf-8"))

    random.shuffle(blocks)
    remaining = [b for b in blocks if random.random() >= args.dropout]
    dropped = [b for b in blocks if b not in remaining]

    print(f"Total loras: {len(blocks)}")
    print(f"Dropout: {args.dropout:.2f}")
    print(f"Remaining: {len(remaining)}")
    print(f"Dropped: {len(dropped)}")
    print()

    print("=== REMAINING LORAS ===")
    for b in remaining:
        print()
        print(b)


if __name__ == "__main__":
    sys.exit(main())
