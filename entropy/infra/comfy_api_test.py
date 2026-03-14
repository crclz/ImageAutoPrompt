from pathlib import Path

from entropy.infra.comfy_api import ComfyApi


def test_run_workflow_happy_case_1():
    # arrange
    template_json_path = Path(__file__).parent / "template.sample.json"
    template_json = template_json_path.read_text("utf8")

    positive = "ocean, tree, sunset, car, (masterpiece, best quality,newest,absurdres,highres)"
    negative = "worst quality, old, early, low quality, lowres, signature, username, logo, bad hands, mutated hands"

    # act
    image_data = ComfyApi.run_workflow("http://localhost:8188", template_json, positive, negative)

    # assert
    assert len(image_data) >= 10

    out_path = Path(__file__).parent / "run_workflow.test.tmp.png"
    out_path.write_bytes(image_data)


# def test_get_workflow_result_no_cache_1():
#     prompt_id = 