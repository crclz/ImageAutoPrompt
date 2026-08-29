r"""
获取 episode 轨迹文件（episode.json）的绝对路径。

用法:
    uv run entropy/cli/get_trajectory.py --episode hello

输出:
    DO NOT EDIT the json.
    C:\...\runs\episodes\hello\episode.json

不读取、不解析、不修改 json 内容，仅输出其绝对位置；LLM 自行按需阅读分析。
episode 不存在时 stderr 报错，exit 1。
"""

import argparse
import sys

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.infra.episode_repository import EpisodeRepository


def main():
    parser = argparse.ArgumentParser(description="get episode trajectory json path")
    parser.add_argument("--episode", required=True, help="episode name")

    args = parser.parse_args()

    try:
        EpisodeRepository.get_eposide(args.episode)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    json_path = (EpisodeRepository.episodes_dir() / args.episode / "episode.json").resolve()
    print("DO NOT EDIT the json.")
    print(json_path)


if __name__ == "__main__":
    main()
