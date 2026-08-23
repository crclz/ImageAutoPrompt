from entropy.domain.services.tag_hinting_service import TagHintingService


def test_get_invalid_tag_hint_shouldReturnEmpty_whenAllTagsValid():
    # arrange
    positives = ["1girl, solo, masterpiece, looking at viewer"]
    negatives = [""]

    # act
    s = TagHintingService.get_invalid_tag_hint(positives, negatives, tolerance=2)

    # assert
    assert s == ""


def test_get_invalid_tag_hint_shouldReturnEmpty_whenInvalidTagCountWithinTolerance():
    # arrange
    positives = ["1girl, solo, masterpiece, reading a red book"]
    negatives = [""]

    # act
    s = TagHintingService.get_invalid_tag_hint(positives, negatives, tolerance=2)

    # assert
    assert s == ""


def test_get_invalid_tag_hint_shouldReturnEmpty_whenInvalidTagCountEqualsTolerance():
    # arrange
    positives = ["1girl, solo, masterpiece, reading a red book, cinematic lightingss"]
    negatives = [""]

    # act
    s = TagHintingService.get_invalid_tag_hint(positives, negatives, tolerance=2)

    # assert
    assert s == ""


def test_get_invalid_tag_hint_shouldReturnHint_whenInvalidTagCountExceedsTolerance():
    # arrange
    positives = ["1girl, solo, masterpiece, reading a red book, cinematic lightingss, raindropsss"]
    negatives = [""]

    # act
    s = TagHintingService.get_invalid_tag_hint(positives, negatives, tolerance=2)

    # assert
    assert s
    assert "prompt[0]" in s
    assert "budget=2" in s
    assert "reading a red book" in s
    assert "cinematic lightingss" in s
    assert "raindropsss" in s


def test_get_invalid_tag_hint_shouldMentionOnlyExceedingPrompts_whenMultiplePrompts():
    # arrange
    positives = [
        "1girl, solo, masterpiece, reading a red book, cinematic lightingss, raindropsss",
        "1girl, solo, masterpiece",
    ]
    negatives = ["", ""]

    # act
    s = TagHintingService.get_invalid_tag_hint(positives, negatives, tolerance=2)

    # assert
    assert "prompt[0]" in s
    assert "prompt[1]" not in s
