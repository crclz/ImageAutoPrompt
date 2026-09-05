import os
import shutil
import time
from pathlib import Path

import pytest

from entropy.domain.services.episode_heartbeat_service import EpisodeHeartbeatService
from entropy.infra.episode_repository import EpisodeRepository

_TEST_EPISODES_DIR = Path("./runs/episodes/tmp_pytest_heartbeat")


@pytest.fixture(autouse=True)
def _redirect_episodes_dir(monkeypatch):
    """重定向 episodes_dir 到 runs/episodes/tmp_pytest_heartbeat，测试结束后整体删除。"""
    monkeypatch.setattr(
        EpisodeRepository, "episodes_dir", classmethod(lambda cls: _TEST_EPISODES_DIR)
    )
    yield
    shutil.rmtree(_TEST_EPISODES_DIR, ignore_errors=True)


def _unique_episode_name() -> str:
    return f"test_heartbeat_{int(time.time() * 1000)}"


def test_EpisodeHeartbeatService_is_really_running_shouldReturnFalse_whenFlagNotExists():
    # arrange
    name = _unique_episode_name()

    # act
    result = EpisodeHeartbeatService.is_really_running(name)

    # assert
    assert result is False


def test_EpisodeHeartbeatService_is_really_running_shouldReturnTrue_whenFlagJustTouched():
    # arrange
    name = _unique_episode_name()
    EpisodeHeartbeatService.touch(name)

    # act
    result = EpisodeHeartbeatService.is_really_running(name)

    # assert
    assert result is True


def test_EpisodeHeartbeatService_is_really_running_shouldReturnFalse_whenFlagMtimeExpired():
    # arrange
    name = _unique_episode_name()
    EpisodeHeartbeatService.touch(name)
    expired_mtime = time.time() - 10  # 10s 前，超过 1s 阈值
    os.utime(EpisodeHeartbeatService.flag_path(name), (expired_mtime, expired_mtime))

    # act
    result = EpisodeHeartbeatService.is_really_running(name)

    # assert
    assert result is False


def test_EpisodeHeartbeatService_clear_shouldRemoveFlag_whenFlagExists():
    # arrange
    name = _unique_episode_name()
    EpisodeHeartbeatService.touch(name)

    # act
    EpisodeHeartbeatService.clear(name)

    # assert
    assert EpisodeHeartbeatService.flag_path(name).exists() is False


def test_EpisodeHeartbeatService_start_heartbeat_shouldMakeIsReallyRunningTrue_whenInsideWithBlock():
    # arrange
    name = _unique_episode_name()

    # act
    with EpisodeHeartbeatService.start_heartbeat(name):
        result = EpisodeHeartbeatService.is_really_running(name)

    # assert
    assert result is True


def test_EpisodeHeartbeatService_start_heartbeat_shouldRemoveFlag_whenWithBlockExits():
    # arrange
    name = _unique_episode_name()

    # act
    with EpisodeHeartbeatService.start_heartbeat(name):
        pass

    # assert
    assert EpisodeHeartbeatService.flag_path(name).exists() is False
