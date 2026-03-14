import logging
from pathlib import Path
import re
from typing import Dict, List

from entropy.domain.models.episode import Episode
from entropy.domain.models.query_model import ImageQueryModel, TimestepQueryModel

_logger = logging.getLogger(__name__)


class EpisodeRepository:
    @classmethod
    def episodes_dir(cls) -> Path:
        d = Path("./runs/episodes")
        d.mkdir(parents=True, exist_ok=True)

        return d

    @staticmethod
    def episode_json() -> str:
        return "episode.json"

    @classmethod
    def get_eposide(cls, name: str) -> Episode:
        d = cls.episodes_dir()
        episode_dir = d / name

        if not episode_dir.exists():
            raise ValueError(f"episode not exist: {name}")

        # read json
        json_file = episode_dir / cls.episode_json()

        if not json_file.exists():
            raise ValueError("episode json not exist")

        json_text = json_file.read_text("utf8")

        return Episode.model_validate_json(json_text)

    @classmethod
    def get_timesteps_query_model(cls, episode_name: str) -> List[TimestepQueryModel]:
        episode = cls.get_eposide(episode_name)

        episode_dir = cls.episodes_dir() / episode_name

        png_files = list(episode_dir.glob("*.png"))
        _logger.debug(f"png_files: {len(png_files)}")

        # t001_05.png
        pattern = r"^t(\d+)_(\d+)\.png$"

        timestep_map: Dict[int, TimestepQueryModel] = {}

        for png_file in png_files:
            match = re.match(pattern, png_file.name)

            _logger.debug(f"name: {png_file.name}, match: {match}")
            if not match:
                continue

            timestep = int(match.group(1))
            image_index = int(match.group(2))

            if timestep >= len(episode.timesteps):
                raise ValueError(f"timestep too big: {png_file}")

            if timestep_map.get(timestep) is None:
                timestep_map[timestep] = TimestepQueryModel(
                    i=timestep,
                    images=[],
                    status=episode.timesteps[timestep].status,
                )

            timestep_map[timestep].images.append(
                ImageQueryModel(image_index=image_index, url=f"/episodes/{episode_name}/files/{png_file.name}")
            )

        # collect timesteps
        timesteps: List[TimestepQueryModel] = []

        for i, timestep in enumerate(episode.timesteps):
            model = timestep_map[i]

            model.chosen_highscores = timestep.chosen_highscores

            # sort images
            model.sort_images()

            timesteps.append(model)

        return timesteps
