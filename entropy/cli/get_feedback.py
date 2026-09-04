"""
获取用户反馈（对齐 Web 端 choose-highscore 的标记结果）。

用法:
    python entropy/cli/get_feedback.py --name hello              # 最新 timestep 的反馈
    python entropy/cli/get_feedback.py --name hello --timestep 1 # 指定 timestep 的反馈

纯查询接口：查询成功一律 exit 0，三态通过文本表达；LLM 自行对比两次输出判断反馈是否变化（没变则停止并向用户二次确认）。

三态:
    已选择:      newest timestep is 1, user choose highscore: timestep_1_image[0], ...
    已提交但没选: newest timestep is 1, user submitted but chose no highscore
    未评价:      newest timestep is 1, user not choose yet
"""

import argparse
import sys

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.infra.episode_repository import EpisodeRepository


def main():
    parser = argparse.ArgumentParser(description="get user feedback")
    parser.add_argument("--name", required=True, help="episode name")
    parser.add_argument("--timestep", type=int, default=None, help="timestep index (default: newest)")

    args = parser.parse_args()

    episode = EpisodeRepository.get_eposide(args.name)

    if args.timestep is None:
        if not episode.timesteps:
            print("episode has no timestep", file=sys.stderr)
            sys.exit(1)

        i = len(episode.timesteps) - 1
        prefix = f"newest timestep is {i}, "
    else:
        i = args.timestep
        if not (0 <= i < len(episode.timesteps)):
            print(f"timestep out of range: {i}", file=sys.stderr)
            sys.exit(1)

        prefix = f"timestep={i}, "

    timestep = episode.timesteps[i]

    if timestep.status == 2:
        if timestep.chosen_highscores:
            scores = ", ".join(h.format_llm() for h in timestep.chosen_highscores)
            print(f"{prefix}user choose highscore: {scores}")
        else:
            print(f"{prefix}user submitted but chose no highscore")
    else:
        print(f"{prefix}user not choose yet")


if __name__ == "__main__":
    main()
