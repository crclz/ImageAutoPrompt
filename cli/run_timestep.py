"""
运行一个 timestep：解析 draft 文件，同步跑完文生图（复用 EpisodeHandler.start_image_processing(join=True)）。

用法:
    uv run cli/run_timestep.py --name hello --draft hello.new_timestep.draft.md

成功流程:
    1. start_image_processing(join=True): 解析 + 拦截检查 + 健康检查 + 状态守卫 + 创建 + 跑完所有图
       - 创建后打印: timestep_{i} created, running (created_hook)
       - 每张图完成时打印: relative_time={分}m{余秒.1位小数}s complete prompt: {idx} (extra_hook)
    2. 全部成功后将 draft 归档到 runs/episodes/{name}/timestep_{i}_{sha256前8位}.md, 并打印:
       draft moved to {相对路径}
    3. exit 0

失败（draft 不存在 / 解析失败 / 无效 tag 拦截 / episode 状态不允许 / 出图失败）:
    stderr 打印提示, exit 1, draft 不动。
"""

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path
# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.http_dtos import StartImageProcessingRequest
from entropy.infra.episode_repository import EpisodeRepository

_t0 = time.time()


def format_relative_time() -> str:
    elapsed = time.time() - _t0
    minutes = int(elapsed // 60)
    seconds = elapsed - minutes * 60
    return f"{minutes}m{seconds:.1f}s"


def main():
    parser = argparse.ArgumentParser(description="run timestep")
    parser.add_argument("--name", required=True, help="episode name")
    parser.add_argument("--draft", required=True, help="draft markdown file path")

    args = parser.parse_args()

    draft_path = Path(args.draft)
    if not draft_path.exists():
        print(f"draft not exist: {draft_path}", file=sys.stderr)
        sys.exit(1)

    draft_text = draft_path.read_text("utf8")

    def created_hook(timestep_i: int) -> None:
        print(f"timestep_{timestep_i} created, running")

    def extra_hook(image_index: int, image_bytes: bytes) -> None:
        print(f"relative_time={format_relative_time()} complete prompt: {image_index}")

    # 同步全流程：解析 + 拦截 + 健康检查 + 创建 + 跑图（失败时 draft 不动、不创建 timestep）
    try:
        EpisodeHandler.start_image_processing(
            StartImageProcessingRequest(episode_name=args.name, exploration_output=draft_text),
            join=True,
            extra_hook=extra_hook,
            created_hook=created_hook,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # 全部成功后归档 draft
    timestep_i = len(EpisodeRepository.get_eposide(args.name).timesteps) - 1
    digest = hashlib.sha256(draft_text.encode("utf8")).hexdigest()[:8]
    dst = EpisodeRepository.episodes_dir() / args.name / f"timestep_{timestep_i}_{digest}.md"

    if Path(dst).exists():
        os.remove(dst)

    draft_path.rename(dst)
    print(f"draft moved to {dst.as_posix()}")


if __name__ == "__main__":
    main()
