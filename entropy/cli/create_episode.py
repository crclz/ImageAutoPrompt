"""
创建 episode（对齐 Web 端 POST /api/create-episode）。

用法:
    uv run entropy/cli/create_episode.py --name hello --workflow entropy/conf/workflows/my-workflow.json --invalid-tag-budget 9999

workflow 与 invalid-tag-budget 在创建时快照进 episode.json，之后以 episode.json 为准（与 app_config 解耦）。
invalid-tag-budget 推荐: noobai=6, anima=9999。

成功: stdout 打印 "episode created: hello", exit 0
失败: stderr 打印原始错误消息（与 Web 端 message 一致）, exit 1
"""

import argparse
import sys
from pathlib import Path

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.application.app_dtos import CreateEpisodeRequest
from entropy.application.episode_handler import EpisodeHandler


def main():
    parser = argparse.ArgumentParser(description="create episode")
    parser.add_argument("--name", required=True, help="episode name")
    parser.add_argument("--workflow", required=True, help="comfy workflow json relative path; run discover_workflows.py to list options")
    parser.add_argument("--invalid-tag-budget", required=True, type=int, help="invalid tag budget (noobai=6, anima=9999)")

    args = parser.parse_args()

    if not Path(args.workflow).exists():
        print(f"workflow not exist: {args.workflow}", file=sys.stderr)
        sys.exit(1)

    try:
        EpisodeHandler.create_episode(
            CreateEpisodeRequest(name=args.name, workflow=args.workflow, invalid_tag_budget=args.invalid_tag_budget)
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print(f"episode created: {args.name}")


if __name__ == "__main__":
    main()
