import pytest

from entropy.domain.services.llm_parse_service import LlmParseService


def test_llm_parse_service_happy_case_1():
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

    positives, negatives = LlmParseService.parse_exploration_output(s)

    assert len(positives) == 4
    assert len(negatives) == 4

    assert positives[0].startswith("1girl")
    assert "artist:torino aqua" in positives[0]
    assert positives[0].endswith("highres")

    assert negatives[0].startswith("worst quality")


def test_llm_parse_service_return_false_when_negative_empty_1():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo

        negative
        ```
    """

    with pytest.raises(ValueError):
        positives, negatives = LlmParseService.parse_exploration_output(s)


def test_llm_parse_service_return_false_when_no_negative():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo
        ```
    """

    with pytest.raises(ValueError):
        positives, negatives = LlmParseService.parse_exploration_output(s)
