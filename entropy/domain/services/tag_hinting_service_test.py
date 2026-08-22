from entropy.domain.services.tag_hinting_service import TagHintingService


# def test_get_invalid_tag_hint_happy_1():
#     # arrange
#     positives = ["1girl, water droplets, raindrops, sitting on stone bridge, cinematic lightingss"]
#     negatives = [""]

#     # act
#     s = TagHintingService.get_invalid_tag_hint(positives, negatives)

#     # assert
#     assert s

#     print("get_invalid_tag_hint return is: \n", s)


# def test_get_invalid_tag_hint_return_empty_when_in_tolerence():
#     # arrange
#     positives = ["1girl, water droplets, raindrops, sitting on stone bridge"]
#     negatives = [""]

#     # act
#     s = TagHintingService.get_invalid_tag_hint(positives, negatives)

#     # assert
#     assert s == ""
