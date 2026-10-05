import pytest

from entropy.domain.models.episode import Episode, EpisodeTimestep, ImagePrompt
from entropy.infra.episode_repository import EpisodeRepository
from entropy.infra.userdata import UserData


@pytest.fixture
def tmp_episode(tmp_path, monkeypatch):
    monkeypatch.setattr(UserData, "episodes_dir", classmethod(lambda cls: tmp_path))

    EpisodeRepository.save_episode(
        "tmp_prompt",
        Episode(
            timesteps=[
                EpisodeTimestep(
                    i=0,
                    status=1,
                    prompts=[
                        ImagePrompt(
                            positive="1girl, solo",
                            negative="worst quality",
                            lora="<lora:foo:1.0>",
                        ),
                        ImagePrompt(positive="1girl, blush", negative=""),
                    ],
                )
            ]
        ),
    )

    images_dir = EpisodeRepository.images_dir("tmp_prompt")
    for file_name in ("t000_00.png", "t000_01.png", "t000_02.png"):
        (images_dir / file_name).write_bytes(b"")

    return "tmp_prompt"


def test_get_timesteps_query_model_shouldAttachPrompt_whenImageIndexWithinPrompts(tmp_episode):
    # act
    timesteps = EpisodeRepository.get_timesteps_query_model(tmp_episode)

    # assert
    images = timesteps[0].images
    assert images[0].prompt == ImagePrompt(
        positive="1girl, solo", negative="worst quality", lora="<lora:foo:1.0>"
    )
    assert images[1].prompt == ImagePrompt(positive="1girl, blush", negative="")


def test_get_timesteps_query_model_shouldLeavePromptUnset_whenImageIndexBeyondPrompts(tmp_episode):
    # act
    timesteps = EpisodeRepository.get_timesteps_query_model(tmp_episode)

    # assert
    assert timesteps[0].images[2].prompt is None
