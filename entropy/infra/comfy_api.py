import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pydantic
import requests
import shortuuid

from entropy.domain.models.app_config import AppConfig

_logger = logging.getLogger(__name__)

# 并发固定为2：并发=1会有浪费的时间（等待单张出图），并发=2刚好不浪费
MAX_WORKERS = 2


class ImageDescriptor(pydantic.BaseModel):
    filename: str = ""
    subfolder: str = ""
    type: str = ""


class ComfyApi:
    @staticmethod
    def _check_cancel(cancellation_source) -> None:
        if cancellation_source is not None and cancellation_source.should_cancel():
            raise ValueError("received cancellation signal")

    @staticmethod
    def render_workflow(
        workflow_template_json: str,
        positive: str,
        negative: str,
        lora: str,
        file_prefix: str,
    ) -> str:
        """
        裸 token 替换：占位符须位于 JSON 字符串内（被一对引号包裹）。
        值经 json.dumps 后剥掉最外层引号注入，保证特殊字符被正确转义，
        因此同时支持 "entropy:positive" 整串与 "entropy:positive, xxx" 子串混排。
        """

        optional_keys = ["entropy:negative", "entropy:lora"]

        replaces = {
            "entropy:positive": positive,
            "entropy:negative": negative,
            "entropy:lora": lora,
            "entropy:output_image": file_prefix,
        }

        rendered_workflow = workflow_template_json

        for k, v in replaces.items():
            if k not in rendered_workflow:
                if k not in optional_keys:
                    raise ValueError(f"workflow not contains: {k}")
                continue

            v = json.dumps(v, ensure_ascii=False)[1:-1]
            rendered_workflow = rendered_workflow.replace(k, v)

        return rendered_workflow

    @staticmethod
    def run_workflow(
        base_url: str,
        workflow_template_json: str,
        positive: str,
        negative: str,
        lora: str = "",
        cancellation_source=None,
    ) -> bytes:
        """
        return: png binary
        """

        assert workflow_template_json

        ComfyApi._check_cancel(cancellation_source)

        # 1. render json

        # force node to execute, avoid cached
        file_prefix = "entropy_out_" + str(shortuuid.uuid())

        rendered_workflow = ComfyApi.render_workflow(workflow_template_json, positive, negative, lora, file_prefix)

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

        deadline = datetime.now(UTC) + timedelta(seconds=AppConfig.read().workflow_timeout_seconds)
        while True:
            ComfyApi._check_cancel(cancellation_source)

            if datetime.now(UTC) > deadline:
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
    def get_workflow_result(base_url: str, prompt_id: str, file_prefix: str) -> tuple[bool, list[ImageDescriptor]]:
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
    def find_output_images(cls, data, file_prefix) -> list[ImageDescriptor]:
        """
        递归遍历 JSON，寻找所有符合 type='output' 且 filename 匹配 pattern 的字典对象。
        """
        results: list[ImageDescriptor] = []

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
        cls,
        base_url: str,
        workflow_template_json: str,
        positives: list[str],
        negative: list[str],
        loras: list[str],
        batch_size=1,
        complete_hook=None,
        cancellation_source=None,
    ) -> list[bytes]:
        """
        return, keep order

        背压提交（参考 batch_v2_job.py 的有界提交窗口设计）：
        Semaphore + 固定并发 MAX_WORKERS，comfy 队列最多 MAX_WORKERS 个在飞，
        提交节奏=执行节奏，不会一次性全部堆积到 comfy 队列。
        """

        assert batch_size == 1, "batchsize not supported"

        assert len(positives) == len(negative)
        assert len(positives) == len(loras)

        results: list[bytes] = [None] * len(positives)  # type: ignore

        sem = threading.Semaphore(MAX_WORKERS)

        def run(i, positive, negative, lora) -> None:
            assert isinstance(i, int)
            assert isinstance(positive, str)
            assert isinstance(negative, str)
            assert isinstance(lora, str)

            try:
                image_bytes = cls.run_workflow(
                    base_url, workflow_template_json, positive, negative, lora, cancellation_source=cancellation_source
                )
                results[i] = image_bytes

                if complete_hook:
                    complete_hook(i, image_bytes)
            finally:
                sem.release()

        with ThreadPoolExecutor(MAX_WORKERS) as executor:
            futures = []

            args_list = zip(range(len(positives)), positives, negative, loras)
            for args in args_list:
                cls._check_cancel(cancellation_source)  # 提交前取消点：不再提交新图
                sem.acquire()  # 窗口满时阻塞在此，保证最多 MAX_WORKERS 在飞（背压）
                futures.append(executor.submit(lambda a=args: run(a[0], a[1], a[2], a[3])))

            # 全部提交完，等待所有任务结束（任一失败即抛出）
            for future in futures:
                future.result()

        for image in results:
            assert image is not None

        return results
