import pytest

from entropy.domain.models.app_config import AppConfig
from entropy.domain.services.draft_parse_service import DraftParseService


def _fake_config(**overrides):
    data = {
        "comfyui_base_url": "http://127.0.0.1:8188",
        "workflow_api_json": "entropy/conf/workflows/dev.json",
        "workflow_timeout_seconds": 180,
        "extra_valid_tag_file": "",
        "port": 5000,
    }
    data.update(overrides)
    return AppConfig.model_validate(data)


def _mock_app_config(monkeypatch, **overrides):
    monkeypatch.setattr(AppConfig, "read", staticmethod(lambda: _fake_config(**overrides)))


def test_parse_timestep_draft_shouldParseMultiplePromptBlocks_whenHappy():
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

    result = DraftParseService.parse_timestep_draft(s)
    positives, negatives, loras = result.positives, result.negatives, result.loras

    assert len(positives) == 4
    assert len(negatives) == 4
    assert len(loras) == 4

    assert positives[0].startswith("1girl")
    assert "artist:torino aqua" in positives[0]
    assert positives[0].endswith("highres")

    assert negatives[0].startswith("worst quality")

    # 旧格式没有 lora 段，应解析为空字符串
    assert loras == [""] * 4


def test_parse_timestep_draft_shouldRaiseValueError_whenNegativeSectionIsEmpty():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo

        negative
        ```
    """

    with pytest.raises(ValueError):
        DraftParseService.parse_timestep_draft(s)


def test_parse_timestep_draft_shouldRaiseValueError_whenNegativeSectionMissing():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo
        ```
    """

    with pytest.raises(ValueError):
        DraftParseService.parse_timestep_draft(s)


def test_parse_timestep_draft_shouldTreatNullNegativeAsEmpty_whenNegativeIsNull():
    s = r"""
        ```prompt0
        positive
        1girl, hatsune miku, solo
        negative
        null
        ```
    """

    result = DraftParseService.parse_timestep_draft(s)
    _, negatives, loras = result.positives, result.negatives, result.loras
    assert negatives[0] == ""
    assert loras == [""]


def test_parse_timestep_draft_shouldReturnLoraValues_whenLoraHappy():
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

    result = DraftParseService.parse_timestep_draft(s)
    positives, negatives, loras = result.positives, result.negatives, result.loras

    assert len(positives) == 2
    assert positives[0].startswith("1girl")
    assert positives[0].endswith("blue eyes")

    assert negatives == ["", ""]

    # prompt0 有 lora；prompt1 lora 段为 null，应置空（与 negative=null 行为对称）
    assert loras[0] == "<lora:noob_mignon:1.0> <lora:noob_real_tweaker:0.9>"
    assert loras[1] == ""


def test_parse_timestep_draft_shouldReturnLoraForEachPrompt_whenAllPromptsHaveLoraSection():
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

    result = DraftParseService.parse_timestep_draft(s)
    positives, negatives, loras = result.positives, result.negatives, result.loras

    assert positives == ["1girl, solo, red hair", "1girl, solo, blue hair"]
    assert negatives == ["", ""]
    assert loras == ["<lora:noob_fkey:0.9>", "<lora:noob_myowa:1.0>"]


def test_parse_timestep_draft_shouldParseFriendlyFormat_whenHappy():
    s = r"""
        : 1girl, solo, red hair
        
        : 1girl, solo, blue hair
    """

    result = DraftParseService.parse_timestep_draft(s)
    assert result.positives == ["1girl, solo, red hair", "1girl, solo, blue hair"]
    assert result.negatives == ["", ""]
    assert result.loras == ["", ""]  # friendly 格式不支持 lora
    assert result.is_friendly is True


def test_parse_exploration_abstract_shouldReturnAbstract_whenExplorationBlockPresent():
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

    abstract = DraftParseService.parse_exploration_abstract(s)
    assert abstract

    assert abstract.type == "artist_only"
    assert abstract.description.startswith("在保持")
    assert abstract.keywords == ["极致逆光", "湿润肉感", "空气感", "唯美通透"]


def test_DraftParseService_image_process_guard_shouldReturnInterceptFalseAndPrompts_whenFriendlyDraftValid(monkeypatch):
    # arrange
    _mock_app_config(monkeypatch)
    s = ": 1girl, solo, red hair"

    # act
    do_intercept, message, prompts = DraftParseService.image_process_guard(s)

    # assert
    assert do_intercept is False
    assert message == ""
    assert len(prompts) == 1
    assert prompts[0].positive == "1girl, solo, red hair"
    assert prompts[0].negative == ""


def test_DraftParseService_image_process_guard_shouldRaiseValueError_whenPromptBlockMissing(monkeypatch):
    # arrange
    _mock_app_config(monkeypatch)
    s = "<exploration>{'type': 'artist_only', 'description': 'd', 'keywords': []}</exploration>"

    # act & assert
    with pytest.raises(ValueError, match="未找到 prompt 块"):
        DraftParseService.image_process_guard(s)


def test_DraftParseService_image_process_guard_shouldRaiseValueError_whenExplorationBlockMissing(monkeypatch):
    # arrange
    _mock_app_config(monkeypatch)
    s = r"""
```prompt0
positive
1girl, solo

negative
null

```
    """

    # act & assert
    with pytest.raises(ValueError, match="缺少 <exploration> 块"):
        DraftParseService.image_process_guard(s)


def test_DraftParseService_image_process_guard_shouldReturnInterceptTrue_whenInvalidTagsExceedTolerance(monkeypatch):
    # arrange
    _mock_app_config(monkeypatch)
    s = ": 1girl, solo, cinematic lightingss, raindropsss"

    # act
    do_intercept, message, prompts = DraftParseService.image_process_guard(s, invalid_tag_budget=1)

    # assert
    assert do_intercept is True
    assert "budget=1" in message
    assert len(prompts) == 1


def test_DraftParseService_image_process_guard_shouldSkipInvalidTagCheck_whenBudgetIsZero(monkeypatch):
    # arrange: 预算为 0（未设置）时，即使存在无效 tag 也不拦截
    _mock_app_config(monkeypatch)
    s = ": 1girl, solo, cinematic lightingss, raindropsss"

    # act
    do_intercept, message, prompts = DraftParseService.image_process_guard(s, invalid_tag_budget=0)

    # assert
    assert do_intercept is False
    assert message == ""
    assert len(prompts) == 1


def test_DraftParseService_image_process_guard_shouldRaiseValueError_whenWorkflowJsonNotExist(monkeypatch):
    # arrange
    _mock_app_config(monkeypatch, workflow_api_json="entropy/conf/workflows/not_exist.json")
    s = ": 1girl, solo"

    # act & assert
    with pytest.raises(ValueError, match="not exist"):
        DraftParseService.image_process_guard(s)
