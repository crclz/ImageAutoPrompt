import pytest

from entropy.application.episode_handler import EpisodeHandler
from entropy.domain.models.episode import ImagePointer
from entropy.application.app_dtos import (
    ChooseHighScoresRequest,
    RollbackTimestepRequest,
    StartImageProcessingRequest,
)

pytestmark = pytest.mark.slow  # 真实 comfy 出图 / 修改真实 episode 数据，默认跳过


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


def test_start_image_processing_happy_1():
    s = r"""
        看来你对 **torino aqua / tiv** 的通透碎光感，以及 **hiten / anmi** 的湿润肉感与逆光氛围非常满意！

        基于这两个 `NewHighScore` 的成功经验，我们在第二阶段（timestep=2）尝试更深入的 **Exploitation（利用）** 与 **Exploration（探索）**：

        1. **Exploitation**：结合这两组画师的长处，尝试 3 名画师的混合，并引入**权重调节**来微调光影与肉感的比例。
        2. **Exploration**：尝试加入 `kantoku`（增强湿身与JK质感）或 `rafaelaaa`（增强宏大叙事的色彩冲击力），看看是否能触碰更高的分数。

        ---

        ```prompt0
        positive
        1girl, hatsune miku, solo, (artist:torino aqua:1.1), (artist:hiten \(hitenkei\):0.9), (artist:tiv:0.8), long hair, looking at viewer, blue eyes, shirt, skirt, hair ornament, thighhighs, holding, closed mouth, bare shoulders, very long hair, twintails, standing, blue hair, white shirt, full body, ahoge, outdoors, pleated skirt, necktie, detached sleeves, sky, sleeveless, ocean, collared shirt, day, black thighhighs, cloud, black skirt, black footwear, blue sky, aqua eyes, zettai ryouiki, sleeveless shirt, floating hair, aqua hair, instrument, black sleeves, guitar, holding instrument, aqua necktie, cumulonimbus cloud, cinematic lighting, tyndall effect, lens flare, water refraction, masterpiece, best quality, newest, absurdres, highres

        negative
        worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands

        ```

        ```prompt1
        positive
        1girl, hatsune miku, solo, (artist:anmi:1.1), (artist:kantoku:0.9), artist:tiv, long hair, looking at viewer, blue eyes, shirt, skirt, hair ornament, thighhighs, holding, closed mouth, bare shoulders, very long hair, twintails, standing, blue hair, white shirt, full body, ahoge, outdoors, pleated skirt, necktie, detached sleeves, sky, sleeveless, ocean, collared shirt, day, black thighhighs, cloud, black skirt, black footwear, blue sky, aqua eyes, zettai ryouiki, sleeveless shirt, floating hair, aqua hair, instrument, black sleeves, guitar, holding instrument, aqua necktie, cumulonimbus cloud, wet, wet clothes, sea spray, masterpiece, best quality, newest, absurdres, highres

        negative
        worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands

        ```

        ```prompt2
        positive
        1girl, hatsune miku, solo, artist:rafaelaaa, artist:torino aqua, long hair, looking at viewer, blue eyes, shirt, skirt, hair ornament, thighhighs, holding, closed mouth, bare shoulders, very long hair, twintails, standing, blue hair, white shirt, full body, ahoge, outdoors, pleated skirt, necktie, detached sleeves, sky, sleeveless, ocean, collared shirt, day, black thighhighs, cloud, black skirt, black footwear, blue sky, aqua eyes, zettai ryouiki, sleeveless shirt, floating hair, aqua hair, instrument, black sleeves, guitar, holding instrument, aqua necktie, cumulonimbus cloud, golden hour, intense backlight, strong rim light, masterpiece, best quality, newest, absurdres, highres

        negative
        worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands

        ```

        ```prompt3
        positive
        1girl, hatsune miku, solo, artist:swd3e2, artist:hiten \(hitenkei\), long hair, looking at viewer, blue eyes, shirt, skirt, hair ornament, thighhighs, holding, closed mouth, bare shoulders, very long hair, twintails, standing, blue hair, white shirt, full body, ahoge, outdoors, pleated skirt, necktie, detached sleeves, sky, sleeveless, ocean, collared shirt, day, black thighhighs, cloud, black skirt, black footwear, blue sky, aqua eyes, zettai ryouiki, sleeveless shirt, floating hair, aqua hair, instrument, black sleeves, guitar, holding instrument, aqua necktie, cumulonimbus cloud, low angle, wide angle, depth of field, masterpiece, best quality, newest, absurdres, highres

        negative
        worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands

        ```

        这一轮我开始使用了括号权重（0.8-1.1），你可以看看带权重的混合是否比第一轮更符合你的心意。如果这四个中有让你惊喜的新风格，请继续反馈！
    """

    response = EpisodeHandler.start_image_processing(
        StartImageProcessingRequest(episode_name="test1", exploration_output=s),
        join=True,
    )

    print("response is", response)


def test_rollback_timestep_happy_1():
    EpisodeHandler.rollback_timestep(RollbackTimestepRequest(episode_name="test_rollback"))
