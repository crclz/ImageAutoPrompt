"""
batch_job — ComfyUI 批量图片处理 CLI 工具。

用法:
    python batch_job.py <job_folder> <port>

示例:
    python batch_job.py ./runs/batch_jobs/test_resize_pic 8188
"""

import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests

# ============================================================
# 常量
# ============================================================

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".jfif", ".avif"}
BATCHJOB_MARKER = ".batchjob."
TIMEOUT_SECONDS = 300
MAX_WORKERS = 2 # 注意这个和timeout有关联
UPLOAD_SUBFOLDER = "batch_job"
PLACEHOLDER_INPUT = "entropy_input_image"
PLACEHOLDER_OUTPUT = "entropy_output_image"

MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jfif": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".avif": "image/avif",
}


# ============================================================
# 主入口
# ============================================================


def main():
    if len(sys.argv) != 3:
        print("用法: python batch_job.py <job_folder> <port>")
        sys.exit(1)

    job_folder = os.path.abspath(sys.argv[1])
    port = sys.argv[2]
    base_url = f"http://localhost:{port}"

    if not os.path.isdir(job_folder):
        print(f"❌ 错误: job_folder 不存在: {job_folder}")
        sys.exit(1)

    # 加载 job.json
    job_json_path = os.path.join(job_folder, "job.json")
    if not os.path.isfile(job_json_path):
        print(f"❌ 错误: {job_json_path} 未找到")
        sys.exit(1)

    with open(job_json_path, "r", encoding="utf-8") as f:
        workflow_template = f.read()

    # 校验占位符
    if PLACEHOLDER_INPUT not in workflow_template:
        print(f"❌ 错误: job.json 缺少占位符 '{PLACEHOLDER_INPUT}'")
        sys.exit(1)
    if PLACEHOLDER_OUTPUT not in workflow_template:
        print(f"❌ 错误: job.json 缺少占位符 '{PLACEHOLDER_OUTPUT}'")
        sys.exit(1)

    # 扫描输入图片
    input_images = _scan_input_images(job_folder)
    if not input_images:
        print("⚠️  警告: 未找到任何输入图片")
        sys.exit(0)

    # 跳过已存在的输出
    skipped: list[str] = []
    to_process: list[str] = []
    for img in input_images:
        out_name = img + BATCHJOB_MARKER + "out.png"
        out_path = os.path.join(job_folder, out_name)
        if os.path.isfile(out_path):
            skipped.append(img)
        else:
            to_process.append(img)

    if skipped:
        print(f"⏭️  跳过 {len(skipped)} 张已处理: {_fmt_list(skipped)}")

    if not to_process:
        print("✅ 所有图片已处理完毕，无需执行。")
        sys.exit(0)

    print(f"📁 job 目录 : {job_folder}")
    print(f"🖼️  输入图片 : {len(input_images)} 张, 待处理 {len(to_process)} 张, 跳过 {len(skipped)} 张")
    print(f"🔧 API 地址 : {base_url}")
    print(f"⚡ 并发数   : {MAX_WORKERS}")
    print("-" * 50)

    # 并发处理
    results: dict[str, list] = {"success": [], "failed": []}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_process_one, base_url, job_folder, workflow_template, img): img
            for img in to_process
        }
        for future in as_completed(futures):
            img = futures[future]
            try:
                ok, msg = future.result()
            except Exception as e:
                ok, msg = False, str(e)
            if ok:
                results["success"].append(img)
                print(f"✅ {img} — {msg}")
            else:
                results["failed"].append((img, msg))
                print(f"❌ {img} — {msg}")

    # 汇总
    print("-" * 50)
    print(f"✅ 成功: {len(results['success'])}")
    print(f"⏭️  跳过: {len(skipped)}")
    print(f"❌ 失败: {len(results['failed'])}")
    if results["failed"]:
        print("失败列表:")
        for img, reason in results["failed"]:
            print(f"  • {img}: {reason}")

    sys.exit(0 if not results["failed"] else 1)


# ============================================================
# 辅助
# ============================================================


def _scan_input_images(job_folder: str) -> list[str]:
    """扫描 job_folder，返回排序后的输入图片文件名列表（排除 .batchjob. 文件和目录）。"""
    images: list[str] = []
    try:
        for name in os.listdir(job_folder):
            full = os.path.join(job_folder, name)
            if not os.path.isfile(full):
                continue
            if BATCHJOB_MARKER in name:
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in EXTENSIONS:
                images.append(name)
    except OSError:
        pass
    images.sort()
    return images


def _fmt_list(items: list[str], max_show: int = 5) -> str:
    """格式化文件名列表，超长省略。"""
    if len(items) <= max_show:
        return ", ".join(items)
    return ", ".join(items[:max_show]) + f" 等 {len(items)} 张"


# ============================================================
# 单张图片处理链路
# ============================================================


def _process_one(base_url: str, job_folder: str, workflow_template: str, image_name: str) -> tuple[bool, str]:
    """处理单张图片的完整链路。返回 (成功与否, 消息)。"""
    try:
        # 1. 上传
        ref = _upload(base_url, os.path.join(job_folder, image_name))

        # 2. 渲染 workflow
        workflow = _render_workflow(workflow_template, ref)

        # 3. 提交 prompt
        prompt_id = _submit(base_url, workflow)

        # 4. 轮询
        img_desc = _poll(base_url, prompt_id)

        # 5. 下载并保存
        out_name = image_name + BATCHJOB_MARKER + "out.png"
        _download(base_url, img_desc, os.path.join(job_folder, out_name))

        return True, "OK"
    except Exception as e:
        return False, str(e)


def _upload(base_url: str, image_path: str) -> str:
    """上传图片到 ComfyUI，返回 LoadImage 引用值（如 'batch_job/abc123.jpg'）。"""
    ext = os.path.splitext(image_path)[1].lower()
    upload_name = uuid.uuid4().hex + ext
    mime = MIME_MAP.get(ext, "application/octet-stream")

    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{base_url}/upload/image",
            files={"image": (upload_name, f, mime)},
            data={
                "overwrite": "true",
                "type": "input",
                "subfolder": UPLOAD_SUBFOLDER,
            },
            timeout=30,
        )

    if not resp.ok:
        raise RuntimeError(f"上传失败 ({resp.status_code}): {resp.text}")

    data = resp.json()
    name = data["name"]
    subfolder = data.get("subfolder", "")
    return f"{subfolder}/{name}" if subfolder else name


def _render_workflow(template: str, loadimage_ref: str) -> object:
    """替换占位符，返回 workflow JSON 对象。"""
    prefix = "batchjob_out_" + uuid.uuid4().hex[:12]

    s = template
    s = s.replace(
        f'"{PLACEHOLDER_INPUT}"',
        json.dumps(loadimage_ref, ensure_ascii=False),
    )
    s = s.replace(
        f'"{PLACEHOLDER_OUTPUT}"',
        json.dumps(prefix, ensure_ascii=False),
    )

    return json.loads(s)


def _submit(base_url: str, workflow: object) -> str:
    """提交 workflow，返回 prompt_id。"""
    resp = requests.post(f"{base_url}/prompt", json={"prompt": workflow}, timeout=10)

    if not resp.ok:
        raise RuntimeError(f"提交失败 ({resp.status_code}): {resp.text}")

    data = resp.json()
    if data.get("node_errors"):
        raise RuntimeError(f"节点错误: {json.dumps(data['node_errors'], ensure_ascii=False)}")

    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise RuntimeError("响应缺少 prompt_id")
    return prompt_id


def _poll(base_url: str, prompt_id: str) -> dict:
    """轮询直到工作流完成，返回 output image descriptor。"""
    deadline = datetime.now() + timedelta(seconds=TIMEOUT_SECONDS)

    while datetime.now() <= deadline:
        time.sleep(1)

        resp = requests.get(f"{base_url}/history/{prompt_id}", timeout=10)
        if not resp.ok:
            continue

        data = resp.json()
        history = data.get(prompt_id)
        if not history:
            continue

        status = history.get("status", {})
        status_str = status.get("status_str", "")

        if "error" in status_str.lower() or "fail" in status_str.lower():
            raise RuntimeError(f"工作流执行失败: {status_str}")

        if status_str != "success":
            continue

        # 递归查找 output image
        desc = _find_output_image(history.get("outputs", {}))
        if desc:
            return desc

        raise RuntimeError("工作流已完成但未找到输出图片")

    raise TimeoutError(f"超时 ({TIMEOUT_SECONDS}s)")


def _find_output_image(data) -> dict | None:
    """递归遍历 JSON，返回第一个 type == 'output' 的 image descriptor。"""
    if isinstance(data, dict):
        if "filename" in data and "type" in data and data.get("type") == "output":
            return {
                "filename": data["filename"],
                "subfolder": data.get("subfolder", ""),
                "type": data["type"],
            }
        for v in data.values():
            result = _find_output_image(v)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_output_image(item)
            if result:
                return result
    return None


def _download(base_url: str, desc: dict, out_path: str):
    """从 ComfyUI 下载输出图片并写入本地。"""
    params = {
        "filename": desc["filename"],
        "subfolder": desc.get("subfolder", ""),
        "type": desc.get("type", "output"),
    }
    resp = requests.get(f"{base_url}/view", params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"下载失败 ({resp.status_code})")
    with open(out_path, "wb") as f:
        f.write(resp.content)


if __name__ == "__main__":
    main()
