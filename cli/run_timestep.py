"""
运行一个 timestep：解析 draft 文件，创建 timestep 并跑文生图（对齐 Web 端 POST /api/episodes/<name>/process-image）。

用法:
    uv run cli/run_timestep.py --name hello --draft hello.new_timestep.draft.md

成功流程:
    1. 将 draft 移动到 runs/episodes/{name}/timestep_{i}_{sha256前8位}.md, 并打印:
       draft moved to {相对路径}
    2. 打印: timestep_{i} created, running
    3. 每张图完成时打印: relative_time={分}m{余秒.1位小数}s complete prompt: {idx}
       (relative_time 是相对于本程序启动时间)
    4. 所有 prompt 跑完后返回, exit 0

失败（draft 不存在 / 解析失败 / 无效 tag 拦截 / episode 状态不允许）:
    stderr 打印提示, exit 1, draft 不动、不创建 timestep。
"""

import argparse
import hashlib
import sys
import time
from pathlib import Path
# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.app_config import AppConfig
from entropy.domain.models.episode import EpisodeTimestep
from entropy.domain.models.http_dtos import StartImageProcessingRequest
from entropy.infra.comfy_api import ComfyApi
from entropy.infra.comfy_health import ComfyHealth
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

    # 解析 + 无效 tag 拦截（失败时 draft 不动、不创建 timestep）
    try:
        do_interception, message, _abstract, prompts, (positives, negatives, loras) = (
            EpisodeHandler.image_process_guard(
                StartImageProcessingRequest(episode_name=args.name, exploration_output=draft_text)
            )
        )
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if do_interception:
        print(message, file=sys.stderr)
        sys.exit(1)

    current_app_config = AppConfig.read()

    # 任何 comfyui 访问前，先健康检查（进程内 10 分钟缓存）
    try:
        ComfyHealth.ensure_comfy_healthy(current_app_config.comfyui_base_url)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # episode 状态守卫
    episode = EpisodeRepository.get_eposide(args.name)
    if not episode.can_process_image():
        print("episode status cannot process image", file=sys.stderr)
        sys.exit(1)

    timestep_i = len(episode.timesteps)

    # 1. 移动 draft 到 episode 目录
    digest = hashlib.sha256(draft_text.encode("utf8")).hexdigest()[:8]
    dst = EpisodeRepository.episodes_dir() / args.name / f"timestep_{timestep_i}_{digest}.md"
    draft_path.rename(dst)
    print(f"draft moved to {dst.as_posix()}")

    # 2. 创建 timestep
    episode.timesteps.append(EpisodeTimestep(i=timestep_i, prompts=prompts))
    EpisodeRepository.save_episode(args.name, episode)
    print(f"timestep_{timestep_i} created, running")

    # 3. 跑所有 prompts
    template_json = Path(current_app_config.workflow_api_json).read_text("utf8")

    def complete_hook(image_index: int, image_bytes: bytes) -> None:
        pic_save_path = EpisodeRepository.pic_path(args.name, timestep_i, image_index)
        pic_save_path.write_bytes(image_bytes)
        print(f"relative_time={format_relative_time()} complete prompt: {image_index}")

    ComfyApi.run_many(
        current_app_config.comfyui_base_url,
        template_json,
        positives,
        negatives,
        loras,
        complete_hook=complete_hook,
    )

    # 4. 所有 prompt 跑完，标记 status=1
    episode = EpisodeRepository.get_eposide(args.name)
    episode.timesteps[timestep_i].status = 1
    EpisodeRepository.save_episode(args.name, episode)


if __name__ == "__main__":
    main()
