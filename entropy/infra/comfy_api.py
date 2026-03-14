from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import logging
import time
from typing import List, Tuple

import requests
import pydantic
import shortuuid


_logger = logging.getLogger(__name__)


class ImageDescriptor(pydantic.BaseModel):
    filename: str = ""
    subfolder: str = ""
    type: str = ""


class ComfyApi:
    @staticmethod
    def run_workflow(base_url: str, workflow_template_json: str, positive: str, negative: str) -> bytes:
        """
        return: png binary
        """

        assert workflow_template_json

        # 1. render json

        # force node to execute, avoid cached
        file_prefix = "entropy_out_" + str(shortuuid.uuid())

        replaces = {
            "entropy:positive": positive,
            "entropy:negative": negative,
            "entropy_out_placeholder": file_prefix,
        }

        rendered_workflow = workflow_template_json

        for k, v in replaces.items():
            k = json.dumps(k, ensure_ascii=False)
            v = json.dumps(v, ensure_ascii=False)

            if k not in rendered_workflow:
                raise ValueError(f"workflow not contains: {k}")

            rendered_workflow = rendered_workflow.replace(k, v)

        _logger.info(f"rendered_workflow is: {rendered_workflow}")

        rendered_workflow_obj = json.loads(rendered_workflow)

        # 2. submit prompt
        base_url = base_url.removesuffix("/")

        response = requests.post(f"{base_url}/prompt", json={"prompt": rendered_workflow_obj}, timeout=10)

        if not response.ok:
            raise ValueError(f"submit prompt failed. code: {response.status_code}, text: {response.text}")

        _logger.info(f"submit prompt response is {response.text}")

        data = response.json()
        assert not data.get("node_errors"), "has node_errors"
        prompt_id = data["prompt_id"]
        assert prompt_id

        _logger.info(f"prompt_id: {prompt_id}. start polling")

        # 3. poll for prompt complete
        deadline = datetime.now() + timedelta(minutes=3)
        while True:
            if datetime.now() > deadline:
                raise ValueError("poll for prompt reached deadline")

            complete, images = ComfyApi.get_workflow_result(base_url, prompt_id, file_prefix)
            if complete:
                assert len(images) == 1, f"output images is not 1: {len(images)}"

                # download image
                image_bytes = ComfyApi.get_image_bytes(base_url, images[0])
                return image_bytes

            time.sleep(1)

    @staticmethod
    def get_image_bytes(base_url: str, image: ImageDescriptor) -> bytes:
        params = {
            "filename": image.filename,
            "subfolder": image.subfolder,
            "type": image.type,
        }

        response = requests.get(f"{base_url}/view", params=params)
        if not response.ok:
            raise ValueError(f"download image error. status: {response.status_code}, text: {response.text}")

        assert isinstance(response.content, bytes)

        return response.content

    @staticmethod
    def get_workflow_result(base_url: str, prompt_id: str, file_prefix: str) -> Tuple[bool, List[ImageDescriptor]]:
        """
        return: false when not complete, true when complete
        throw: when failure
        """

        response = requests.get(f"{base_url}/history/{prompt_id}", timeout=10)
        if not response.ok:
            raise ValueError(f"get prompt history failed. code: {response.status_code}, text: {response.text}")

        _logger.debug(f"history response: {response.text}")

        response_data = response.json()

        history = response_data.get(prompt_id)
        if not history:
            return False, []

        status_job = history.get("status")
        if not status_job:
            return False, []

        status_str = status_job.get("status_str", "")
        if "error" in status_str or "fail" in status_str:
            raise ValueError(f"prompt run failed: {prompt_id}. status_str: {status_str}")

        if status_str != "success":
            return False, []

        # parse ImageDescriptor
        images = ComfyApi.find_output_images(history["outputs"], file_prefix)
        return True, images

    @classmethod
    def find_output_images(cls, data, file_prefix) -> List[ImageDescriptor]:
        """
        递归遍历 JSON，寻找所有符合 type='output' 且 filename 匹配 pattern 的字典对象。
        """
        results: List[ImageDescriptor] = []

        if isinstance(data, dict):
            # 健壮性检查：判断当前字典是否同时包含 filename 和 type
            if "filename" in data and "type" in data:
                if data["type"] == "output" and data["filename"].startswith(file_prefix):
                    # 找到目标，返回包含完整信息的字典
                    results.append(
                        ImageDescriptor(
                            filename=data["filename"], subfolder=data.get("subfolder", ""), type=data["type"]
                        )
                    )

            # 继续递归遍历字典的所有值
            for value in data.values():
                results.extend(cls.find_output_images(value, file_prefix))

        elif isinstance(data, list):
            # 遍历列表项
            for item in data:
                results.extend(cls.find_output_images(item, file_prefix))

        return results

    @classmethod
    def run_many(
        cls, base_url: str, workflow_template_json: str, positives: List[str], negative: List[str], batch_size=1
    ) -> List[bytes]:
        """
        return, keep order
        """

        assert batch_size == 1, "batchsize not supported"

        # multi thread
        assert len(positives) == len(negative)

        results: List[bytes] = [None] * len(positives)  # type: ignore

        def run(i, positive, negative) -> None:
            assert isinstance(i, int)
            assert isinstance(positive, str)
            assert isinstance(negative, str)

            if i > 0:
                # useless, but makes me feel better
                time.sleep(i * 0.5)

            image_bytes = cls.run_workflow(base_url, workflow_template_json, positive, negative)
            results[i] = image_bytes

        with ThreadPoolExecutor(10) as executor:
            args_list = zip(range(len(positives)), positives, negative)
            a = executor.map(lambda x: run(x[0], x[1], x[2]), args_list)
            a = list(a)  # wait

        for image in results:
            assert image is not None

        return results
