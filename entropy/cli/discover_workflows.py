"""
列出全部可选的 comfy workflow json（相对路径），供 create_episode.py 的 --workflow 使用。

用法:
    uv run entropy/cli/discover_workflows.py

输出（一行一个相对路径）:
    entropy/conf/workflows/anima.json
    ...

选项列表 = entropy/conf/workflows 目录下的所有 *.json，与 web 端创建 episode 时的下拉框一致。
"""

import argparse
import sys

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.application.episode_handler import EpisodeHandler


def main():
    parser = argparse.ArgumentParser(description="discover workflow jsons")
    parser.parse_args()

    for wf in EpisodeHandler.list_workflow_paths():
        print(wf)


if __name__ == "__main__":
    main()
