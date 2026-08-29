---
name: install-environment
description: 安装本仓库的 python 运行环境。uv（主推）与传统 python 环境两条路线。当用户要求"安装环境"或提到 install-environment 时使用。
---

## 目标

安装完成后，仓库根目录可运行：

- uv 路线: `uv run server.py`
- python 路线: `python server.py`

## 流程

### 1. 询问用户

<ask-user need-user-confirmation="force" max-questions-per-time="2">
1. 路线: uv（推荐，无需预装 python，一条 uv sync 搞定）还是已有 python 环境（conda/venv/系统 python，需 >= 3.12）？
2. 是否需要 RAG 功能（tag 灵感与纠错，见 README 末尾）？RAG 依赖较重（torch 数 GB）；不需要则裁剪依赖，安装快得多。
</ask-user>

### 2. （仅当不需要 RAG）裁剪依赖

编辑 pyproject.toml：

- dependencies 中注释掉 `chromadb`、`modelscope`、`sentence-transformers`、`torch` 四项
- 文件尾部一并注释 `[[tool.uv.index]]` 的 pytorch-cu126 段与 `[tool.uv.sources]` 的 torch 行（torch 专属下载源）

依据: torch 无代码直接依赖，仅是 sentence-transformers 的传递依赖；chromadb / sentence-transformers 是 rag_service 内的 lazy import，裁剪后 server 正常启动，仅 RAG 功能不可用。

### 3a. uv 路线

<ask-user need-user-confirmation="force" max-questions-per-time="1">
1. 是否需要中国大陆加速（pypi 镜像 + python 解释器镜像）？
</ask-user>

1. `uv --version` 检查；未安装则按官方指引安装: https://docs.astral.sh/uv/getting-started/installation/
2. 需加速时: 先按 [references/china-mainland-uv.md](references/china-mainland-uv.md) 配置镜像
3. 仓库根目录执行 `uv sync`（未裁剪 RAG 时，torch 为 cu126 版，体积大、耗时长属正常）
4. 验证: `uv run python -c "import flask; print('ok')"`

### 3b. python 环境路线

<ask-user need-user-confirmation="force" max-questions-per-time="3">
1. 使用什么 python 环境（conda / venv / 系统 python）？
2. 是否需要中国大陆加速（pip 清华源）？
3. （仅未裁剪 RAG 时）torch 是否需要 CUDA 版？
</ask-user>

1. 确认所选环境中 `python --version` >= 3.12
2. 仓库根目录执行 `pip install toml && python export_requirements.py`（生成 requirements.txt；若已裁剪 RAG，导出结果自动不含 RAG 依赖）
3. `pip install -r requirements.txt`（需加速时加清华源 `-i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`；需 CUDA 版 torch 时先按 https://pytorch.org 单独装 torch）
4. 验证: `python -c "import flask; print('ok')"`

### 4. 收尾

- 告知用户启动命令（见"目标"）
- 若裁剪了 RAG: 告知将来启用方法（取消 pyproject.toml 中相应注释后重新 `uv sync`，建库见 docs/install-rag.md）
- 引导下一步: 执行 setup-app-config skill 配置 `entropy/conf/app_config.yaml`
