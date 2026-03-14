from entropy.domain.models.query_model import EpisodeQueryModel
from entropy.infra.episode_repository import EpisodeRepository


class EpisodeHandler:
    @classmethod
    def episodes_list_page(cls) -> None:
        """
        In this page, episodes are listed. Order by create_time desc.
        Episodes are managed using folder structure.
        Main data is in episode.json
        """
        raise NotImplementedError()

    @classmethod
    def new_episode(cls) -> None:
        """
        start new episode
        """
        raise NotImplementedError()

    @classmethod
    def episode_page(cls):
        """
        this page accept query parameter: name
        and show:
        - timesteps and images
        - high score images (highlight)

        these data are refreshed frequently, by polling get_episode_data via page
        """
        raise NotImplementedError()

    @classmethod
    def get_episode_data_wrapper(cls):
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel json
        """
        raise NotImplementedError()

    @classmethod
    def get_episode_data(cls, name: str) -> EpisodeQueryModel:
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel
        """

        timesteps = EpisodeRepository.get_timesteps_query_model(name)

        return EpisodeQueryModel(timesteps=timesteps)

    @classmethod
    def choose_best_scores(cls):
        """
        change EpisodeTimestep.status from 1 to 2
        """
        raise NotImplementedError()

    @classmethod
    def get_timestep_observation(cls):
        """
        return a string e.g.
        timestep=15
        user: NewHighScore: timestep_14_image[0]
        """
        raise NotImplementedError()

    @classmethod
    def start_image_processing(cls):
        """
        change EpisodeTimestep.status from 0 to 1.
        when done, change EpisodeTimestep.status from 1 to 2.
        user can force state go back to 0.
        """
        raise NotImplementedError()
