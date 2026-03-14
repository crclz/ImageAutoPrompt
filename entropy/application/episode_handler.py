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
    def get_episode_data(cls):
        """
        get data, which could be rendered on webpages. return EpisodeQueryModel json
        """
        raise NotImplementedError()

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
        return immediately and keep running in background.
        when done, change EpisodeTimestep.status from 1 to 2.
        """
        raise NotImplementedError()
