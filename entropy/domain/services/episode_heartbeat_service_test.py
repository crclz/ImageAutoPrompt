import os
import time

from entropy.domain.services.episode_heartbeat_service import EpisodeHeartbeatService


def _unique_episode_name() -> str:
    return f"test_heartbeat_{int(time.time() * 1000)}"


def test_EpisodeHeartbeatService_is_really_running_shouldReturnFalse_whenFlagNotExists():
    # arrange
    name = _unique_episode_name()

    # act
    result = EpisodeHeartbeatService.is_really_running(name)

    # assert
    assert result is False

    # cleanup
    EpisodeHeartbeatService.clear(name)


def test_EpisodeHeartbeatService_is_really_running_shouldReturnTrue_whenFlagJustTouched():
    # arrange
    name = _unique_episode_name()
    EpisodeHeartbeatService.touch(name)

    # act
    result = EpisodeHeartbeatService.is_really_running(name)

    # assert
    assert result is True

    # cleanup
    EpisodeHeartbeatService.clear(name)


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

    # cleanup
    EpisodeHeartbeatService.clear(name)


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
