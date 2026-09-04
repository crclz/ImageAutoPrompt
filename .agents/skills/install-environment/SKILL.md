---
name: install-environment
description: 安装本仓库的 python 运行环境。uv（主推）与传统 python 环境两条路线。当用户要求"安装环境"或提到 install-environment 时使用。
---

## 目标

安装完成后，仓库根目录可运行 `python server.py`（`python` 指 .venv 解释器，路径规则见 AGENTS.md 的 `## python` 节）。

## 依赖分组（uv 相关知识唯一权威出处，其他文档引用本 skill）

pyproject 已将 RAG 依赖固化在 `[dependency-groups] rag`（chromadb、modelscope、sentence-transformers、torch；torch 走 cu126 专属源）:

- 轻量: `uv sync --no-group rag` —— server 与常规开发够用，仅 RAG 功能不可用
- 全量: `uv sync` —— 含 torch cu126，体积数 GB；仅当需要 RAG（rag 网页、semantic-tag-search）才装
- 全量环境误跑 `uv sync --no-group rag` 会卸掉 RAG 包（`ai_models/` 与 `database/` 不受影响，重新 `uv sync` 即可恢复）

是否需要 RAG 是安装时的一次性决策，由本 skill 通过询问用户完成。安装完成后日常开发只用 .venv 的 python（路径规则见 AGENTS.md `## python` 节），不再需要 uv。

## 流程

### 1. 询问用户

<ask-user need-user-confirmation="force" max-questions-per-time="2">
1. 路线: uv（推荐，无需预装 python，一条 uv sync 搞定）还是已有 python 环境（conda/venv/系统 python，需 >= 3.12）？
2. 是否需要 RAG 功能（tag 灵感与纠错，见 README 末尾）？RAG 依赖在 pyproject 的 rag 组（torch 数 GB）；不需要则装轻量环境，快得多。
</ask-user>

### 2a. uv 路线

<ask-user need-user-confirmation="force" max-questions-per-time="1">
1. 是否需要中国大陆加速（pypi 镜像 + python 解释器镜像）？
</ask-user>

1. `uv --version` 检查；未安装则按官方指引安装: https://docs.astral.sh/uv/getting-started/installation/
2. 需加速时: 先按 [references/china-mainland-uv.md](references/china-mainland-uv.md) 配置镜像
3. 仓库根目录执行:
   - 不需要 RAG: `uv sync --no-group rag`
   - 需要 RAG: `uv sync`（含 torch cu126，体积大、耗时长属正常）
4. 验证: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import flask; print('ok')"`（Linux/macOS 为 `.venv/bin/python`）

### 2b. python 环境路线

<ask-user need-user-confirmation="force" max-questions-per-time="3">
1. 使用什么 python 环境（conda / venv / 系统 python）？
2. 是否需要中国大陆加速（pip 清华源）？
3. （仅需要 RAG 时）torch 是否需要 CUDA 版？
</ask-user>

1. 确认所选环境中 `python --version` >= 3.12
2. 仓库根目录执行 `pip install toml && python export_requirements.py`（默认导出轻量依赖；需 RAG 时加 `--rag`，导出结果含 rag 组）
3. `pip install -r requirements.txt`（需加速时加清华源 `-i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`；需 CUDA 版 torch 时先按 https://pytorch.org 单独装 torch）
4. 验证: `python -c "import flask; print('ok')"`

### 3. 收尾

- 告知用户启动命令: `python server.py`
- 若装了轻量环境: 告知将来启用 RAG 的方法（`uv sync` 全量安装后，按 docs/install-rag.md 建库）
- 引导下一步: 执行 setup-app-config skill 配置 `entropy/conf/app_config.yaml`
