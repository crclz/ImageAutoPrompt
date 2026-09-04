"""
运行一个 timestep：解析 draft 文件，同步跑完文生图（join 后台线程等待完成）。

用法:
    python entropy/cli/run_timestep.py --name hello --draft hello.7k2f.new_timestep.draft.md

成功流程:
    1. start_image_processing: 解析 + 拦截检查 + 健康检查 + 状态守卫 + 创建 + 后台线程跑图
       - 创建后打印: timestep_{i} created, running (created_hook)
       - 每张图完成时打印: relative_time={分}m{余秒.1位小数}s complete prompt: {idx} (extra_hook)
    2. join 等待跑图结束，全部成功后将 draft 归档到 runs/episodes/{name}/timestep_{i}_{sha256前8位}.md
    3. exit 0

失败（draft 不存在 / 解析失败 / 无效 tag 拦截 / episode 状态不允许）:
    stderr 打印提示, exit 1, draft 不动。

跑图失败（含取消）:
    跑图线程收尾：timestep 置为 done 并记录 error，draft 不归档；exit 1（取消为 exit 130）。

Ctrl+C:
    主线程捕获 KeyboardInterrupt → 发送取消信号（写 cancel_flag）→ 等待跑图线程收尾 → exit 130。
    web 端也可对同一 episode 发送取消信号。
"""

import argparse
import hashlib
import os
import signal
import sys
import time
from pathlib import Path
from threading import Thread

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.domain.services.timestep_draft_consumption_service import TimestepDraftConsumptionService
from entropy.infra.cancellation import send_cancel
from entropy.infra.episode_repository import EpisodeRepository


def interruptable_join_thread(thread: Thread) -> None:
    """可中断的线程等待。

    Windows 上无限 join 会吞掉 Ctrl+C：主线程阻塞在 C 层等待，
    pending 的 KeyboardInterrupt 无法处理（延迟到线程退出才抛）。
    循环小 timeout join：每次返回后主线程有机会处理信号，Ctrl+C 可及时抛出。
    """
    while thread.is_alive():
        thread.join(timeout=0.2)


class RunTimestepCliProgram:
    """无状态 CLI 程序：run(episode_name, draft_path) -> exit code（0 成功 / 1 失败 / 130 取消）。"""

    @staticmethod
    def run(episode_name: str, draft_path: Path) -> int:
        draft_text = RunTimestepCliProgram._read_draft(draft_path)

        t0 = time.time()

        def format_relative_time() -> str:
            elapsed = time.time() - t0
            minutes = int(elapsed // 60)
            seconds = elapsed - minutes * 60
            return f"{minutes}m{seconds:.1f}s"

        def created_hook(timestep_i: int) -> None:
            print(f"timestep_{timestep_i} created, running")

        def extra_hook(image_index: int, image_bytes: bytes) -> None:
            print(f"relative_time={format_relative_time()} complete prompt: {image_index}")

        failed: list[str] = []

        def done_hook(error) -> None:
            if error:
                print("meet exception. transfered timestep_i status to done and saved error info.", file=sys.stderr)
                failed.append(error)

        # 同步全流程：解析 + 拦截 + 健康检查 + 创建 + 跑图（失败时 draft 不动）
        try:
            thread = TimestepDraftConsumptionService.start_image_processing(
                episode_name,
                draft_text,
                extra_hook=extra_hook,
                created_hook=created_hook,
                done_hook=done_hook,
            )
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1

        cancelled: list[bool] = []
        cancel_flag_path = EpisodeRepository.episodes_dir() / episode_name / "cancel_flag"

        def sigint_handler(signum, frame):
            # Windows 上 KeyboardInterrupt 依赖主线程字节码间隙，主线程阻塞在 join 时会被延迟；
            # 劫持 SIGINT：handler 立即执行，写取消信号后由跑图线程在下个取消点收尾。
            print("SIGINT captured: sending cancel signal", file=sys.stderr)
            send_cancel(cancel_flag_path)
            cancelled.append(True)

        signal.signal(signal.SIGINT, sigint_handler)

        RunTimestepCliProgram._wait_for_completion(thread, cancel_flag_path, cancelled)

        if cancelled:
            print("timestep cancelled", file=sys.stderr)
            return 130

        if failed:
            print(f"run failed: {failed[0]}", file=sys.stderr)
            return 1

        RunTimestepCliProgram._archive_draft(draft_path, draft_text, episode_name)
        return 0

    @staticmethod
    def _read_draft(draft_path: Path) -> str:
        if not draft_path.exists():
            print(f"draft not exist: {draft_path}", file=sys.stderr)
            sys.exit(1)

        return draft_path.read_text("utf8")

    @staticmethod
    def _wait_for_completion(thread: Thread, cancel_flag_path: Path, cancelled: list[bool]) -> None:
        try:
            interruptable_join_thread(thread)
        except KeyboardInterrupt:
            # 兜底：SIGINT handler 未覆盖到的极端情况
            send_cancel(cancel_flag_path)
            interruptable_join_thread(thread)

    @staticmethod
    def _archive_draft(draft_path: Path, draft_text: str, episode_name: str) -> None:
        # 全部成功后归档 draft（调试用：文件名含 dont_move 时不移动）
        if "dont_move" in draft_path.name:
            print(f"draft not moved (dont_move in filename): {draft_path.as_posix()}")
            sys.exit(0)

        timestep_i = len(EpisodeRepository.get_eposide(episode_name).timesteps) - 1
        digest = hashlib.sha256(draft_text.encode("utf8")).hexdigest()[:8]
        dst = EpisodeRepository.episodes_dir() / episode_name / f"timestep_{timestep_i}_{digest}.md"

        if Path(dst).exists():
            os.remove(dst)

        draft_path.rename(dst)
        print(f"draft moved to {dst.as_posix()}")


def main():
    parser = argparse.ArgumentParser(description="run timestep")
    parser.add_argument("--name", required=True, help="episode name")
    parser.add_argument("--draft", required=True, help="draft markdown file path")

    args = parser.parse_args()

    print("提示: 若本次运行失败，draft 文件不会被移动。可直接原地修改 draft md 后重新执行本命令；只有全部成功后 draft 才会被归档到 episode 目录。", flush=True)
    sys.exit(RunTimestepCliProgram.run(args.name, Path(args.draft)))


if __name__ == "__main__":
    main()
