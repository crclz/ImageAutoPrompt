"""
查看 userdata 的实际位置与它的判断过程（人可直接读，agent 也可直接调用）。

用法（必须在仓库根目录执行）:
    python entropy/cli/locate_userdata.py

输出约定:
    - 判断过程、推导出的绝对路径、各路径 exists/missing 全部走 stderr（给人看）
    - stdout 只有最后一行：userdata 的绝对路径（给脚本/agent 取值，如 `... | tail -1` 或 `$(...)`）

判断链（只有这一条，没有环境变量）:
    1. 仓库根的 `userdata_pointer` 文件内容（一行绝对路径）
    2. 该文件不存在或为空 → 默认 `./userdata`（绝对化后输出）
"""

import argparse
import sys
from pathlib import Path

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.infra import userdata
from entropy.infra.userdata import DEFAULT, ENTRIES, POINTER, UserData


def _pointer_raw() -> str | None:
    """指针文件内容（strip 后）；文件不存在返回 None，存在但为空返回空串。"""
    if not userdata.USERDATA_POINTER_PATH.is_file():
        return None
    return userdata.USERDATA_POINTER_PATH.read_text("utf8").strip()


def _require_repo_root() -> None:
    """cwd 不是仓库根直接失败：默认值与 userdata_pointer 都以仓库根为基准。"""
    repo_root = userdata.REPO_ROOT
    if Path.cwd().resolve() != repo_root:
        print(f"错误: 必须在仓库根目录运行（当前 cwd: {Path.cwd()}，仓库根: {repo_root}）", file=sys.stderr)
        print("用法: cd 到仓库根后执行 `python entropy/cli/locate_userdata.py`", file=sys.stderr)
        sys.exit(1)


def _print_trace(raw: str | None) -> None:
    default_path = (userdata.REPO_ROOT / "userdata").resolve()

    if raw is None:
        shown_raw = "(文件不存在)"
    else:
        shown_raw = raw if raw else "(文件存在但为空)"

    step_pointer = f"1. {userdata.USERDATA_POINTER_PATH.name:<16} : {shown_raw}"
    step_default = f"2. 默认 ./userdata{'':<7} : {default_path}"

    try:
        resolved, source = UserData.locate()
    except ValueError as e:
        print("userdata 判断过程:", file=sys.stderr)
        print(f"  {step_pointer}   <- 无效", file=sys.stderr)
        print(f"  {step_default}", file=sys.stderr)
        print(f"\n错误: {e}", file=sys.stderr)
        raise SystemExit(1) from None

    if source == POINTER:
        step_pointer += "   <- used"
    else:
        step_default += "   <- used"

    print("userdata 判断过程:", file=sys.stderr)
    print(f"  {step_pointer}", file=sys.stderr)
    print(f"  {step_default}", file=sys.stderr)
    print(f"\nresolved: {resolved}  (root: {'exists' if resolved.is_dir() else 'missing'})", file=sys.stderr)

    for label, name in ENTRIES.items():
        path = resolved / name
        print(f"  {label:<17} {path}  ({'exists' if path.exists() else 'missing'})", file=sys.stderr)

    if source == DEFAULT and raw is not None:
        print("\n注意: userdata_pointer 存在但内容为空，已回退默认 ./userdata", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="显示 userdata 的位置与判断过程")
    parser.parse_args()

    _require_repo_root()

    raw = _pointer_raw()
    _print_trace(raw)

    print(UserData.locate()[0])  # stdout 只此一行：绝对路径（_print_trace 已保证不会 raise）


if __name__ == "__main__":
    main()
