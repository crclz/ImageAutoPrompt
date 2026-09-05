"""get_loras.py 的单元测试（default 级：无网络、无真实库文件）。"""

import importlib.util
import sys
from pathlib import Path

import yaml

_SCRIPT = Path(__file__).parent / "get_loras.py"
_spec = importlib.util.spec_from_file_location("get_loras", _SCRIPT)
get_loras = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(get_loras)


def test_parse_rating_valid_tokens():
    for token in get_loras.VALID_RATINGS:
        assert get_loras.parse_rating(f"<{token}> 顶级") == token


def test_parse_rating_unrated_token():
    assert get_loras.parse_rating("<未评> 报告有下载记录") == "未评"


def test_parse_rating_invalid():
    assert get_loras.parse_rating("顶级") is None
    assert get_loras.parse_rating("5> 顶级") is None
    assert get_loras.parse_rating(None) is None
    assert get_loras.parse_rating(123) is None


def _sample_loras():
    return {
        "a": {"my_comment": "<5> 顶级"},
        "b": {"my_comment": "<1> 不适合"},
        "c": {"my_comment": "<3+> 有特色"},
        "d": {"my_comment": "<未评> 孤儿"},
        "e": {"my_comment": "表现一般"},
        "f": {"my_comment": "<3-> 质量小问题"},
        "g": {"my_comment": "<5-> 次顶级"},
        "h": {},
    }


def test_build_pool_filters_and_sorts():
    pool, unrated = get_loras.build_pool(_sample_loras())
    assert sorted(pool) == ["a", "c", "g"]
    assert sorted(unrated) == ["e", "h"]


def test_main_end_to_end(tmp_path, monkeypatch, capsys):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "anima_loras.yaml").write_text(
        yaml.safe_dump({"loras": _sample_loras()}, allow_unicode=True), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["get_loras.py", "--arch=anima", "--limit=2"])

    get_loras.main()

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert len(lines) == 2
    names = {line.removeprefix("<lora:").removesuffix(">") for line in lines}
    assert names <= {"a", "c", "g"}
    assert "later: e, h" in captured.err
