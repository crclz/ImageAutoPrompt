from pathlib import Path

from entropy.infra.comfy_api import ComfyApi

test_base_address = "http://localhost:8188"


def test_run_workflow_happy_case_1():
    # arrange
    template_json_path = Path(__file__).parent / "template.sample.json"
    template_json = template_json_path.read_text("utf8")

    positive = "ocean, tree, sunset, car"
    negative = ""

    # act
    image_data = ComfyApi.run_workflow(test_base_address, template_json, positive, negative)

    # assert
    assert len(image_data) >= 10

    out_path = Path(__file__).parent / "run_workflow.test.tmp.png"
    out_path.write_bytes(image_data)


def test_get_workflow_result_no_cache_1():
    prompt_id = "86804727-6e4a-43f2-8a93-e19499ff77d7"
    file_prefix = "entropy-out-2b0c34db-b0fa-4d0f-af2f-7beb8af23e55"

    # act
    complete, images = ComfyApi.get_workflow_result(test_base_address, prompt_id, file_prefix)
    assert complete

    assert images

    print("images", images)


def test_run_many_happy_1():
    template_json_path = Path(__file__).parent / "template.sample.json"
    template_json = template_json_path.read_text("utf8")

    positive = "ocean, tree, sunset, car, (masterpiece, best quality,newest,absurdres,highres)"
    negative = "worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands"

    positives = [positive] * 4
    negatives = [negative] * 4

    positives[0] = "helicopter, " + positives[0]

    images = ComfyApi.run_many(test_base_address, template_json, positives, negatives)
    assert len(images) == 4

    for i, image_bytes in enumerate(images):
        out_path = Path(__file__).parent / f"run_many_{i}.tmp.png"
        out_path.write_bytes(image_bytes)
