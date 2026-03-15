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

    @staticmethod
    def save_episode(name: str, episode: Episode) -> None:
        d = EpisodeRepository.episodes_dir()
        episode_dir = d / name

        if not episode_dir.exists():
            raise ValueError(f"episode not exist: {name}")

        # read json
        json_file = episode_dir / EpisodeRepository.episode_json()

        json_string = episode.model_dump_json(indent=4)

        json_file.write_text(json_string, "utf8")

    @classmethod
    def get_timesteps_query_model(cls, episode_name: str) -> List[TimestepQueryModel]:
        episode = cls.get_eposide(episode_name)

        episode_dir = cls.episodes_dir() / episode_name

        png_files = list(episode_dir.glob("*.png"))
        # _logger.debug(f"png_files: {len(png_files)}")

        # t001_05.png
        pattern = r"^t(\d+)_(\d+)\.png$"

        timestep_map: Dict[int, TimestepQueryModel] = {}

        # initialize
        for timestep in episode.timesteps:
            timestep_map[timestep.i] = TimestepQueryModel(
                i=timestep.i,
                images=[],
                status=timestep.status,
                rag_result=timestep.rag_result,
                rag_wip=timestep.rag_wip,
            )

        for png_file in png_files:
            match = re.match(pattern, png_file.name)

            _logger.debug(f"name: {png_file.name}, match: {match}")
            if not match:
                continue

            timestep = int(match.group(1))
            image_index = int(match.group(2))

            if timestep >= len(episode.timesteps):
                continue  # ignore these files
                # raise ValueError(f"timestep too big: {png_file}")

            if timestep_map.get(timestep) is None:
                raise ValueError(f"png file exceed timestep: {png_file}")

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

    @classmethod
    def pic_path(cls, episode_name: str, timestep: int, image_index: int) -> Path:
        d = cls.episodes_dir() / episode_name
        f = f"t{timestep:03d}_{image_index:02d}.png"

        return d / f

    @classmethod
    def timestep_pics(cls, episode_name: str, target_timestep: int) -> List[Path]:
        episode_dir = cls.episodes_dir() / episode_name

        png_files = list(episode_dir.glob("*.png"))
        pattern = r"^t(\d+)_(\d+)\.png$"

        results: List[Path] = []

        for png_file in png_files:
            match = re.match(pattern, png_file.name)

            if not match:
                continue

            timestep = int(match.group(1))
            image_index = int(match.group(2))

            if timestep == target_timestep:
                results.append(png_file)

        return results
