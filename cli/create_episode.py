"""
创建 episode（对齐 Web 端 POST /api/create-episode）。

用法:
    PYTHONPATH="." uv run cli/create_episode.py --name hello

成功: stdout 打印 "episode created: hello", exit 0
失败: stderr 打印原始错误消息（与 Web 端 message 一致）, exit 1
"""

import argparse
import sys

from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.http_dtos import CreateEpisodeRequest


def main():
    parser = argparse.ArgumentParser(description="create episode")
    parser.add_argument("--name", required=True, help="episode name")

    args = parser.parse_args()

    try:
        EpisodeHandler.create_episode(CreateEpisodeRequest(name=args.name))
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print(f"episode created: {args.name}")


if __name__ == "__main__":
    main()
