import logging
from pathlib import Path
import re
from typing import Dict, List, Tuple

from entropy.domain.models.app_config import AppConfig
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
    def images_dir(cls, episode_name: str) -> Path:
        """从 ./runs/episodes/{episode}/ 切换到 ./runs/episodes/{episode}/images/"""
        d = cls.episodes_dir() / episode_name / "images"
        d.mkdir(parents=True, exist_ok=True)
        return d

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
            episode_dir.mkdir()

        # read json
        json_file = episode_dir / EpisodeRepository.episode_json()

        json_string = episode.model_dump_json(indent=4)

        json_file.write_text(json_string, "utf8")

    @classmethod
    def get_timesteps_query_model(cls, episode_name: str) -> List[TimestepQueryModel]:
        episode = cls.get_eposide(episode_name)

        # 修改：从新的 images 目录获取图片
        img_dir = cls.images_dir(episode_name)
        png_files = list(img_dir.glob("*.png"))

        # t001_05.png
        pattern = r"^t(\d+)_(\d+)\.png$"

        timestep_map: Dict[int, TimestepQueryModel] = {}

        # initialize
        for timestep in episode.timesteps:
            initial_md_prefix = ""

            if timestep.i == 0:
                initial_md_prefix = Path(AppConfig.read().prompt_file).read_text("utf8")
                if not initial_md_prefix.endswith("\n"):
                    initial_md_prefix += "\n"

            timestep_map[timestep.i] = TimestepQueryModel(
                i=timestep.i,
                images=[],
                initial_md_prefix=initial_md_prefix,
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

            if timestep_map.get(timestep) is None:
                # 如果图片超出范围，此处选择忽略或根据业务逻辑处理
                continue

            # 修改：URL 路径增加 /images/ 段
            timestep_map[timestep].images.append(
                ImageQueryModel(image_index=image_index, url=f"/episodes/{episode_name}/files/images/{png_file.name}")
            )

        # collect timesteps
        timesteps: List[TimestepQueryModel] = []

        for i, timestep in enumerate(episode.timesteps):
            model = timestep_map.get(i)
            if not model:
                continue

            model.chosen_highscores = timestep.chosen_highscores

            # sort images
            model.sort_images()

            timesteps.append(model)

        return timesteps

    @classmethod
    def pic_path(cls, episode_name: str, timestep: int, image_index: int) -> Path:
        # 修改：使用 images_dir
        d = cls.images_dir(episode_name)
        f = f"t{timestep:03d}_{image_index:02d}.png"

        return d / f

    @classmethod
    def timestep_pics(cls, episode_name: str, target_timestep: int) -> List[Path]:
        # 修改：使用 images_dir
        img_dir = cls.images_dir(episode_name)

        png_files = list(img_dir.glob("*.png"))
        pattern = r"^t(\d+)_(\d+)\.png$"

        results: List[Path] = []

        for png_file in png_files:
            match = re.match(pattern, png_file.name)

            if not match:
                continue

            timestep = int(match.group(1))

            if timestep == target_timestep:
                results.append(png_file)

        return results

    @classmethod
    def list_episodes(cls) -> List[Tuple[str, Episode]]:
        """遍历所有子文件夹，加载包含 episode.json 的 Episode"""
        episodes: List[Tuple[str, Episode]] = []
        base_dir = cls.episodes_dir()

        # 遍历基础目录下的所有项
        for item in base_dir.iterdir():
            # 只有是文件夹且内部包含 episode.json 才进行加载
            if item.is_dir() and (item / cls.episode_json()).exists():
                try:
                    # 复用已有的 get_eposide 方法
                    episode = cls.get_eposide(item.name)
                    episodes.append((item.name, episode))
                except Exception as e:
                    _logger.error(f"Failed to load episode from {item.name}: {e}")

        # 可选：根据需要进行排序（例如按名称或时间）
        # episodes.sort(key=lambda x: x.name)

        return episodes
