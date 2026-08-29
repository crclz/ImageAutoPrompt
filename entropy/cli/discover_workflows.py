"""
列出全部可选的 comfy workflow json（相对路径），供 create_episode.py 的 --workflow 使用。

用法:
    uv run entropy/cli/discover_workflows.py

输出（一行一个相对路径，default 标记 app_config 配置的默认工作流）:
    reading config file: entropy/conf/app_config.yaml, knowing workflow_api_json = entropy/conf/workflows/my-workflow.json
    default: entropy/conf/workflows/my-workflow.json
    entropy/conf/workflows/my-workflow.json
    ...

选项列表 = 默认工作流同级目录下的所有 *.json，与 web 端创建 episode 时的下拉框一致。
"""

import argparse
import sys

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.app_config import AppConfig


def main():
    parser = argparse.ArgumentParser(description="discover workflow jsons")
    parser.parse_args()

    default_workflow, options = EpisodeHandler.list_workflow_paths()

    print(f"reading config file: {AppConfig.CONFIG_PATH}, knowing workflow_api_json = {default_workflow}")
    print(f"default: {default_workflow}")
    for wf in options:
        print(wf)


if __name__ == "__main__":
    main()
