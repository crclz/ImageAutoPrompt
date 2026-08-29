import json
from pathlib import Path

import pytest

from entropy.infra.comfy_api import ComfyApi

test_base_address = "http://localhost:8188"

minimal_template = '{"4": {"inputs": {"text": "entropy:positive"}}, "9": {"inputs": {"filename_prefix": "entropy:output_image"}}}'


def test_render_workflow_standalone_1():
    # act
    rendered = ComfyApi.render_workflow(minimal_template, "1girl, solo", "lowres", "", "entropy_out_abc123")

    # assert
    obj = json.loads(rendered)
    assert obj["4"]["inputs"]["text"] == "1girl, solo"
    assert obj["9"]["inputs"]["filename_prefix"] == "entropy_out_abc123"


def test_render_workflow_substring_mixed_1():
    # arrange
    template = '{"4": {"inputs": {"text_0": "entropy:positive,masterpiece, best quality"}}, "9": {"inputs": {"filename_prefix": "entropy:output_image"}}}'

    # act
    rendered = ComfyApi.render_workflow(template, "1girl, solo", "lowres", "", "entropy_out_abc123")

    # assert
    obj = json.loads(rendered)
    assert obj["4"]["inputs"]["text_0"] == "1girl, solo,masterpiece, best quality"


def test_render_workflow_escape_special_chars_1():
    # arrange
    positive = '1girl, "quote", back\\slash'

    # act
    rendered = ComfyApi.render_workflow(minimal_template, positive, "", "", "entropy_out_abc123")

    # assert
    obj = json.loads(rendered)
    assert obj["4"]["inputs"]["text"] == positive


def test_render_workflow_missing_required_1():
    # arrange
    template_missing_output = '{"4": {"inputs": {"text": "entropy:positive"}}}'
    template_missing_positive = '{"9": {"inputs": {"filename_prefix": "entropy:output_image"}}}'

    # act & assert
    with pytest.raises(ValueError, match="entropy:output_image"):
        ComfyApi.render_workflow(template_missing_output, "1girl", "", "", "entropy_out_abc")

    with pytest.raises(ValueError, match="entropy:positive"):
        ComfyApi.render_workflow(template_missing_positive, "1girl", "", "", "entropy_out_abc")


def test_render_workflow_optional_missing_ok_1():
    # act: 模板不含 entropy:negative / entropy:lora，不报错
    rendered = ComfyApi.render_workflow(minimal_template, "1girl, solo", "lowres", "some_lora", "entropy_out_abc123")

    # assert
    obj = json.loads(rendered)
    assert obj["4"]["inputs"]["text"] == "1girl, solo"


def test_render_workflow_optional_present_empty_1():
    # arrange
    template = '{"4": {"inputs": {"text": "entropy:positive"}}, "6": {"inputs": {"lora": "entropy:lora"}}, "9": {"inputs": {"filename_prefix": "entropy:output_image"}}}'

    # act
    rendered = ComfyApi.render_workflow(template, "1girl", "", "", "entropy_out_abc123")

    # assert
    obj = json.loads(rendered)
    assert obj["6"]["inputs"]["lora"] == ""


@pytest.mark.slow  # 真实访问 ComfyUI 出图
def test_run_workflow_happy_case_1():
    # arrange
    template_json_path = Path("entropy/conf/workflows/dev_fast.json")
    template_json = template_json_path.read_text("utf8")

    positive = "ocean, tree, sunset, car"
    negative = ""

    # act
    image_data = ComfyApi.run_workflow(test_base_address, template_json, positive, negative)

    # assert
    assert len(image_data) >= 10

    out_path = Path(__file__).parent / "run_workflow.test.tmp.png"
    out_path.write_bytes(image_data)


@pytest.mark.slow  # 真实访问 ComfyUI
def test_get_workflow_result_no_cache_1():
    prompt_id = "86804727-6e4a-43f2-8a93-e19499ff77d7"
    file_prefix = "entropy-out-2b0c34db-b0fa-4d0f-af2f-7beb8af23e55"

    # act
    complete, images = ComfyApi.get_workflow_result(test_base_address, prompt_id, file_prefix)
    assert complete

    assert images

    print("images", images)


@pytest.mark.slow  # 真实访问 ComfyUI 出图
def test_run_many_happy_1():
    template_json_path = Path("entropy/conf/workflows/dev_fast.json")
    template_json = template_json_path.read_text("utf8")

    positive = "ocean, tree, sunset, car, (masterpiece, best quality,newest,absurdres,highres)"
    negative = "worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands"

    positives = [positive] * 4
    negatives = [negative] * 4
    loras = [""] * 4

    positives[0] = "helicopter, " + positives[0]

    images = ComfyApi.run_many(test_base_address, template_json, positives, negatives, loras)
    assert len(images) == 4

    for i, image_bytes in enumerate(images):
        out_path = Path(__file__).parent / f"run_many_{i}.tmp.png"
        out_path.write_bytes(image_bytes)
