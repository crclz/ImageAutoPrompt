"""
batch_v2_job — ComfyUI 文本参数笛卡尔积批量生成 CLI 工具。

用法:
    uv run batch_v2_job.py <job_folder> <port>

示例:
    uv run batch_v2_job.py ./runs/batch_jobs2/test_job_1 8188

说明:
    不接收图片输入。以 job.yaml 声明的变量矩阵做笛卡尔积，
    对每个组合渲染 workflow.json（替换 ${var} 与 entropy_output_image），
    生成 output/out_*.png。
"""

import itertools
import json
import os
import re
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests
import yaml

# ============================================================
# 常量
# ============================================================

PLACEHOLDER_OUTPUT = "entropy_output_image"
TIMEOUT_SECONDS = 300
MAX_WORKERS = 2
OUTPUT_SUBDIR = "output"

# 文件名非法字符（Windows 通用）及控制字符
_FILENAME_BAD_CHARS = re.compile(r'[/\\:*?"<>|\x00-\x1f]')
_VAR_TOKEN_RE = re.compile(r"\$\{([^}]+)\}")


# ============================================================
# 主入口
# ============================================================


def main():
    if len(sys.argv) != 3:
        print("用法: uv run batch_v2_job.py <job_folder> <port>")
        sys.exit(1)

    job_folder = os.path.abspath(sys.argv[1])
    port = sys.argv[2]
    base_url = f"http://localhost:{port}"

    if not os.path.isdir(job_folder):
        print(f"❌ 错误: job_folder 不存在: {job_folder}")
        sys.exit(1)

    # 加载并校验 workflow.json
    workflow_json_path = os.path.join(job_folder, "workflow.json")
    if not os.path.isfile(workflow_json_path):
        print(f"❌ 错误: {workflow_json_path} 未找到")
        sys.exit(1)
    with open(workflow_json_path, "r", encoding="utf-8") as f:
        workflow_template = f.read()
    if PLACEHOLDER_OUTPUT not in workflow_template:
        print(f"❌ 错误: workflow.json 缺少占位符 '{PLACEHOLDER_OUTPUT}'")
        sys.exit(1)

    # 加载并解析 job.yaml
    job_yaml_path = os.path.join(job_folder, "job.yaml")
    if not os.path.isfile(job_yaml_path):
        print(f"❌ 错误: {job_yaml_path} 未找到")
        sys.exit(1)
    with open(job_yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    vars_meta, var_order, flag_var = _parse_vars(cfg)

    # 场景 B：job.yaml 定义了变量但 workflow 完全没用 → 失败
    for var in var_order:
        if f"${{{var}}}" not in workflow_template:
            print(f"❌ 错误: job.yaml 定义了变量 '{var}' 但 workflow.json 未使用（缺少 ${{{var}}}）")
            sys.exit(1)

    # 场景 A：workflow 里有 ${var} 但 job.yaml 未定义 → 忽略 + 警告
    defined = set(var_order)
    for tok in _VAR_TOKEN_RE.findall(workflow_template):
        if tok not in defined:
            print(f"⚠️  警告: workflow.json 含未定义变量 '${{{tok}}}'，已忽略（job.yaml 为准）")

    # 值 key 合法性校验
    for var in var_order:
        for key in vars_meta[var]["data"]:
            _validate_key(var, key)

    # 生成组合
    combos = _build_combos(vars_meta, var_order)

    # 整理输出目录 & 跳过
    out_dir = os.path.join(job_folder, OUTPUT_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    skipped: list[str] = []
    to_process: list[tuple] = []
    for combo in combos:
        relpath = _combo_relpath(var_order, combo, flag_var)
        out_path = os.path.join(out_dir, relpath)
        if os.path.isfile(out_path):
            skipped.append(relpath)
        else:
            to_process.append((combo, relpath))

    if skipped:
        print(f"⏭️  跳过 {len(skipped)} 个已生成: {_fmt_list(skipped)}")

    if not to_process:
        print("✅ 所有组合已生成完毕，无需执行。")
        sys.exit(0)

    print(f"📁 job 目录 : {job_folder}")
    print(f"🧩 组合总数 : {len(combos)} , 待处理 {len(to_process)} , 跳过 {len(skipped)}")
    if flag_var:
        print(f"📂 子文件夹 : 按 '{flag_var}' 分文件夹输出")
    print(f"🔧 API 地址 : {base_url}")
    print(f"⚡ 并发数   : {MAX_WORKERS}")
    print("-" * 50)

    # 有界提交窗口执行（errgroup 效果）
    sem = threading.Semaphore(MAX_WORKERS)
    results: dict[str, list] = {"success": [], "failed": []}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for combo, relpath in to_process:
            sem.acquire()

            def _run(c=combo, rp=relpath):
                try:
                    _process_one(base_url, workflow_template, vars_meta, var_order, c, out_dir, rp)
                    status = "success"
                    msg = "OK"
                except Exception as e:  # noqa: BLE001
                    status = "failed"
                    msg = str(e)
                finally:
                    sem.release()
                return status, rp, msg

            future = executor.submit(_run)
            status, rp, msg = future.result()
            if status == "success":
                results["success"].append(rp)
                print(f"✅ {rp} — {msg}")
            else:
                results["failed"].append((rp, msg))
                print(f"❌ {rp} — {msg}")

    # 汇总
    print("-" * 50)
    print(f"✅ 成功: {len(results['success'])}")
    print(f"⏭️  跳过: {len(skipped)}")
    print(f"❌ 失败: {len(results['failed'])}")
    if results["failed"]:
        print("失败列表:")
        for name, reason in results["failed"]:
            print(f"  • {name}: {reason}")

    sys.exit(0 if not results["failed"] else 1)


# ============================================================
# 解析 & 组合
# ============================================================


def _parse_vars(cfg):
    """解析 job.yaml，返回 (vars_meta, var_order, flag_var)。

    vars_meta[var] = {"data": {key: value}, "out_new_folder": bool}
    flag_var: 标记了 out_new_folder=true 的变量名（至多一个），否则为 None。
    """
    if not cfg or "vars" not in cfg:
        print("❌ 错误: job.yaml 缺少顶层 'vars' 字段")
        sys.exit(1)

    vars_meta = {}
    var_order = []
    for var, spec in cfg["vars"].items():
        if not isinstance(spec, dict) or "data" not in spec:
            print(f"❌ 错误: 变量 '{var}' 必须包含 'data' 字段")
            sys.exit(1)
        data = spec["data"]
        if not isinstance(data, dict) or not data:
            print(f"❌ 错误: 变量 '{var}' 的 'data' 必须是非空映射")
            sys.exit(1)
        vars_meta[var] = {
            "data": dict(data),
            "out_new_folder": bool(spec.get("out_new_folder", False)),
        }
        var_order.append(var)

    flags = [var for var in var_order if vars_meta[var]["out_new_folder"]]
    if len(flags) > 1:
        print(f"❌ 错误: 最多只能有一个变量设置 out_new_folder=true，当前有 {len(flags)} 个: {_fmt_list(flags)}")
        sys.exit(1)
    flag_var = flags[0] if flags else None

    return vars_meta, var_order, flag_var


def _validate_key(var: str, key: str):
    """校验值 key 可安全用作文件名/文件夹片段，非法则报错退出。"""
    if not key or _FILENAME_BAD_CHARS.search(key):
        print(f"❌ 错误: 变量 '{var}' 的值 key '{key!r}' 含非法文件名字符，无法用于输出")
        sys.exit(1)


def _build_combos(vars_meta, var_order):
    """按 job.yaml 变量顺序生成笛卡尔积组合列表。"""
    keys_lists = [list(vars_meta[var]["data"].keys()) for var in var_order]
    return list(itertools.product(*keys_lists))


def _combo_relpath(var_order, combo, flag_var):
    """根据组合生成输出相对路径。

    - 若存在标志变量 flag_var，其 {var}_{key} 段变成子文件夹，文件名只保留其余变量段
      且 out_ 前缀永远保留；若没有其余变量，文件名即为 out.png。
    - 否则与旧行为一致：out_{var}_{key}_....png。
    """
    folder = None
    file_parts: list[str] = []
    for var, key in zip(var_order, combo):
        if var == flag_var:
            folder = f"{var}_{key}"
        else:
            file_parts.extend([var, key])

    filename = "out" + ("_" + "_".join(file_parts) if file_parts else "") + ".png"
    return os.path.join(folder, filename) if folder else filename


def _fmt_list(items: list[str], max_show: int = 5) -> str:
    if len(items) <= max_show:
        return ", ".join(items)
    return ", ".join(items[:max_show]) + f" 等 {len(items)} 个"


# ============================================================
# 单组合处理链路
# ============================================================


def _process_one(base_url, workflow_template, vars_meta, var_order, combo, out_dir, relpath):
    """处理单个组合的完整链路（渲染→提交→轮询→下载保存）。"""
    # 1. 渲染 workflow
    workflow = _render_workflow(workflow_template, vars_meta, var_order, combo)

    # 2. 提交
    prompt_id = _submit(base_url, workflow)

    # 3. 轮询（按唯一前缀匹配输出）
    desc = _poll(base_url, prompt_id)

    # 4. 下载保存（确保子文件夹存在）
    out_path = os.path.join(out_dir, relpath)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    _download(base_url, desc, out_path)


def _render_workflow(template, vars_meta, var_order, combo):
    """替换 ${var} 与 entropy_output_image，返回 workflow JSON 对象。

    替换规则：对变量值做 json.dumps(ensure_ascii=False) 后剥掉最外层引号，
    注入到字符串内容里（模板中 ${var} 必须被一对引号包着）。
    如下保证字符串内部特殊字符仍被正确转义。
    """
    # 唯一前缀，用于定位输出
    prefix = "batch_v2_out_" + uuid.uuid4().hex[:12]

    s = template

    # 替换 ${var}：json.dumps 后剥最外层一对引号
    for var, key in zip(var_order, combo):
        value = vars_meta[var]["data"][key]
        dumped = json.dumps(value, ensure_ascii=False)
        s = s.replace(f"${{{var}}}", dumped[1:-1])

    # 替换输出占位符（等价于剥引号的裸替换）
    s = s.replace(
        f'"{PLACEHOLDER_OUTPUT}"',
        json.dumps(prefix, ensure_ascii=False),
    )

    return json.loads(s)


def _submit(base_url, workflow) -> str:
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


def _poll(base_url, prompt_id) -> dict:
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


def _download(base_url, desc, out_path):
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