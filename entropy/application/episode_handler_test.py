from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.episode import ImagePointer
from entropy.domain.models.http_dtos import ChooseHighScoresRequest


def test_get_episode_data_happy_1():

    name = "test1"

    data = EpisodeHandler.get_episode_data(name)

    print("data is", data.model_dump_json())


def test_choose_high_scores_happy_1():

    EpisodeHandler.choose_high_scores(
        ChooseHighScoresRequest(
            name="test1",
            timestep=1,
            highscores=[ImagePointer(timestep=1, image_index=0)],
        )
    )
