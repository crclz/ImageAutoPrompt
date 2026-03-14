from entropy.application.episode_handler import EpisodeHandler


def test_get_episode_data_happy_1():

    name = "test1"

    data = EpisodeHandler.get_episode_data(name)

    print("data is", data.model_dump_json())
