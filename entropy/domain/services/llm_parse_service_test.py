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

    positives, negatives, loras, _ = LlmParseService.parse_exploration_output(s)

    assert len(positives) == 4
    assert len(negatives) == 4
    assert len(loras) == 4

    assert positives[0].startswith("1girl")
    assert "artist:torino aqua" in positives[0]
    assert positives[0].endswith("highres")

    assert negatives[0].startswith("worst quality")

    # 旧格式没有 lora 段，应解析为空字符串
    assert loras == [""] * 4


def test_llm_parse_service_return_false_when_negative_empty_1():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo

        negative
        ```
    """

    with pytest.raises(ValueError):
        LlmParseService.parse_exploration_output(s)


def test_llm_parse_service_return_false_when_no_negative():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo
        ```
    """

    with pytest.raises(ValueError):
        LlmParseService.parse_exploration_output(s)


def test_llm_parse_service_return_true_when_negative_empty():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo
        negative
        null
        ```
    """

    positives, negatives, loras, _ = LlmParseService.parse_exploration_output(s)
    assert negatives[0] == ""
    assert loras == [""]


def test_llm_parse_service_with_lora():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo, long hair, looking at viewer, blue eyes

        negative
        null

        lora
        <lora:noob_mignon:1.0> <lora:noob_real_tweaker:0.9>
        ```

        ```prompt1
        positive
        1girl, hatsune miku, solo

        negative
        null

        lora
        null
        ```
    """

    positives, negatives, loras, _ = LlmParseService.parse_exploration_output(s)

    assert len(positives) == 2
    assert positives[0].startswith("1girl")
    assert positives[0].endswith("blue eyes")

    assert negatives == ["", ""]

    # prompt0 有 lora；prompt1 lora 段为 null，应置空（与 negative=null 行为对称）
    assert loras[0] == "<lora:noob_mignon:1.0> <lora:noob_real_tweaker:0.9>"
    assert loras[1] == ""


def test_llm_parse_service_lora_only_some_prompts():
    s = r"""
        ```prompt0
        positive
        1girl, solo, red hair

        negative
        null

        lora
        <lora:noob_fkey:0.9>
        ```

        ```prompt1
        positive
        1girl, solo, blue hair

        negative
        null

        lora
        <lora:noob_myowa:1.0>
        ```
    """

    positives, negatives, loras, _ = LlmParseService.parse_exploration_output(s)

    assert positives == ["1girl, solo, red hair", "1girl, solo, blue hair"]
    assert negatives == ["", ""]
    assert loras == ["<lora:noob_fkey:0.9>", "<lora:noob_myowa:1.0>"]


def test_llm_parse_service_user_manually_input_friendly():
    s = r"""
        : 1girl, solo, red hair
        
        : 1girl, solo, blue hair
    """

    positives, negatives, loras, is_friendly = LlmParseService.parse_exploration_output(s)
    assert positives == ["1girl, solo, red hair", "1girl, solo, blue hair"]
    assert negatives == ["", ""]
    assert loras == ["", ""]  # friendly 格式不支持 lora
    assert is_friendly is True


def test_danbooru_search():
    s = r"""
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

        ```danbooru_search
        {
            "query_list": ["a", "b", "c"]
        }
        ```


        这一轮我开始使用了括号权重（0.8-1.1），你可以看看带权重的混合是否比第一轮更符合你的心意。如果这四个中有让你惊喜的新风格，请继续反馈！
    """

    query_list = LlmParseService.parse_danbooru_search(s)
    assert ["a", "b", "c"] == query_list


def test_exploration_abstract_1():
    s = r"""
你好！收到你的需求。目前我们正处于探索的初始阶段（timestep=0），你的原始 prompt 描绘了一个非常经典的秋季校园场景：春日野穹、银杏叶、围巾与制服。

由于你明确要求**先保持其他不变，只探索画风**，我将进入 `artist_only` 模式。我选择了四种截然不同的画风走向：从极致通透的逆光，到充满肉感的官能美，再到带有忧郁气息的水彩感和华丽的萌系美学。

```exploration
{
    "type": "artist_only",
    "description": "在保持春日野穹秋季校园场景不变的基础上，探索四种差异化的画风：1. torino aqua 的极致逆光与透明感；2. kantoku 的湿润肉感与JK美学；3. fly 的忧郁水彩氛围感；4. anmi 的轻盈唯美商业感。旨在测试你对不同光影和材质表现的偏好。",
    "keywords": ["极致逆光", "湿润肉感", "空气感", "唯美通透"]
}

```

```prompt0
positive
1girl, solo, kasugano sora, artist:torino aqua, long hair, looking at viewer, shirt, skirt, long sleeves, thighhighs, ribbon, closed mouth, very long hair, sitting, twintails, jacket, school uniform, white shirt, grey hair, ahoge, hair ribbon, outdoors, pleated skirt, necktie, shoes, black thighhighs, black footwear, bag, scarf, black jacket, tree, zettai ryouiki, plaid, black ribbon, leaf, blazer, loafers, grey skirt, school bag, red scarf, autumn leaves, plaid scarf, autumn, ginkgo leaf

negative
null

```
    """

    abstract = LlmParseService.parse_exploration_abstract(s)
    assert abstract

    assert abstract.type == "artist_only"
    assert abstract.description.startswith("在保持")
    assert abstract.keywords == ["极致逆光", "湿润肉感", "空气感", "唯美通透"]
