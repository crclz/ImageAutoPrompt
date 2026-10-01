"""locate_userdata.py 与 UserData.locate() 的单元测试（default 级：无网络、无真实数据）。"""

import sys
from pathlib import Path

import pytest

from entropy.cli import locate_userdata
from entropy.infra import userdata


@pytest.fixture
def fake_pointer(tmp_path, monkeypatch):
    """把指针文件与"仓库根"都换到 tmp_path，返回 (指针文件, 默认 userdata 目录)。"""
    pointer = tmp_path / "repo" / "userdata_pointer"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(userdata, "USERDATA_POINTER_PATH", pointer)
    monkeypatch.setattr(userdata, "REPO_ROOT", pointer.parent)
    return pointer, pointer.parent / "userdata"


def test_locate_uses_pointer_when_present(fake_pointer, tmp_path):
    pointer, _default = fake_pointer
    target = tmp_path / "ext"
    pointer.write_text(str(target), encoding="utf8")

    assert userdata.UserData.locate() == (target, userdata.POINTER)


def test_locate_falls_back_to_default_when_pointer_missing(fake_pointer):
    _pointer, default = fake_pointer

    assert userdata.UserData.locate() == (default.resolve(), userdata.DEFAULT)


def test_locate_falls_back_to_default_when_pointer_empty(fake_pointer):
    pointer, default = fake_pointer
    pointer.write_text("\n", encoding="utf8")

    assert userdata.UserData.locate() == (default.resolve(), userdata.DEFAULT)


def test_locate_raises_when_pointer_is_relative(fake_pointer):
    pointer, _default = fake_pointer
    pointer.write_text("my_userdata", encoding="utf8")

    with pytest.raises(ValueError, match="必须是绝对路径"):
        userdata.UserData.locate()


def test_cli_stdout_is_only_the_absolute_path(fake_pointer, tmp_path, monkeypatch, capsys):
    pointer, _default = fake_pointer
    target = tmp_path / "ext"
    pointer.write_text(str(target), encoding="utf8")
    monkeypatch.chdir(pointer.parent)
    monkeypatch.setattr(sys, "argv", ["locate_userdata.py"])

    locate_userdata.main()

    captured = capsys.readouterr()
    assert captured.out.strip() == str(target)
    assert len(captured.out.strip().splitlines()) == 1  # agent 可安全 `| tail -1`
    assert "userdata_pointer" in captured.err  # 判断过程给人看
    assert "episodes/" in captured.err  # 推导出的子路径逐条列出


def test_cli_exits_nonzero_when_pointer_is_relative(fake_pointer, monkeypatch, capsys):
    pointer, _default = fake_pointer
    pointer.write_text("relative/path", encoding="utf8")
    monkeypatch.chdir(pointer.parent)
    monkeypatch.setattr(sys, "argv", ["locate_userdata.py"])

    with pytest.raises(SystemExit) as e:
        locate_userdata.main()

    assert e.value.code == 1
    assert "必须是绝对路径" in capsys.readouterr().err


def test_cli_refuses_to_run_outside_repo_root(fake_pointer, tmp_path, monkeypatch, capsys):
    _pointer, _default = fake_pointer
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["locate_userdata.py"])

    with pytest.raises(SystemExit) as e:
        locate_userdata.main()

    assert e.value.code == 1
    assert "必须在仓库根目录运行" in capsys.readouterr().err


def test_userdata_derived_paths_hang_off_the_root(fake_pointer, tmp_path):
    pointer, _default = fake_pointer
    target = tmp_path / "ext"
    pointer.write_text(str(target), encoding="utf8")
    monkeypatch_target = target

    assert userdata.UserData.episodes_dir() == monkeypatch_target / "episodes"
    assert userdata.UserData.workflows_dir() == monkeypatch_target / "workflows"
    assert userdata.UserData.cache_dir() == monkeypatch_target / "cache"
    assert userdata.UserData.app_config_path() == monkeypatch_target / "app_config.yaml"
    assert userdata.UserData.lora_library_path("anima") == monkeypatch_target / "anima_loras.yaml"


def test_repo_root_is_a_real_repo():
    assert (userdata.REPO_ROOT / "pyproject.toml").is_file()
    assert userdata.REPO_ROOT == Path(__file__).resolve().parents[2]
