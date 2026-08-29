r"""
获取 episode 轨迹文件（episode.json）的绝对路径。

用法:
    uv run entropy/cli/get_trajectory.py --episode hello

输出:
    DO NOT EDIT the json.
    C:\...\runs\episodes\hello\episode.json
    （随后附 json 结构说明，便于 LLM 直接阅读分析）

不读取、不解析、不修改 json 内容，仅输出其绝对位置与结构说明；LLM 自行按需阅读分析。
episode 不存在时 stderr 报错，exit 1。
"""

import argparse
import sys

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.infra.episode_repository import EpisodeRepository

SCHEMA_HINT = """json 结构说明（// 后为字段说明，仅供阅读）:
{
    "create_time": 1787991105,          // unix 时间戳
    "workflow": "entropy/conf/workflows/my-workflow.json",  // 本 episode 固定的工作流（创建时快照；空=旧episode回退app_config）
    "invalid_tag_budget": 9999,         // 无效tag预算（创建时快照；0=不校验）
    "timesteps": [
        {
            "i": 0,                      // timestep 序号，从 0 递增
            "status": 2,                 // 0=跑图中, 1=跑完待反馈, 2=已选定高分
            "chosen_highscores": [       // 用户标记的高分图（status=2 时有效）
                {"timestep": 0, "image_index": 3}
            ],
            "error": "",                 // 失败原因；空=成功
            "stacktrace": "",            // 失败时的完整堆栈
            "prompts": [                 // 与 draft 中 promptN 一一对应，下标即 image_index
                {"positive": "...", "negative": "", "lora": ""}
            ]
        }
    ]
}"""


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
    print("DO NOT EDIT the json.", flush=True)
    print(json_path, flush=True)
    print()
    print(SCHEMA_HINT)


if __name__ == "__main__":
    main()
