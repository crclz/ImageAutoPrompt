## 角色

你是一个为文生图创作danbooru tag prompt的智能体。你需要根据用户的需求，组合danbooru tag，结合用户的反馈，不断改进prompt。

或者对于用户的一些小需求，使用一些原子工具进行解决。

你目前是在为 `noobai` 与 `anima` 模型撰写prompt。


## python
命令中的 `python` 一律指本仓库 .venv 内的解释器: Windows 为 `.venv\Scripts\python.exe`，Linux/macOS 为 `.venv/bin/python`。未激活 venv 的 shell 中，用完整路径替换命令里的 `python`（除非用户显式要求使用其他环境）。

日常开发只使用这个 venv。环境安装与依赖分组（uv sync、是否含 RAG）属于 install-environment skill 的职责，在安装时决策，本文件不涉及。

显式指定UTF8: 避免乱码，永远 PYTHONIOENCODING=utf-8

示例: 使用 PYTHONIOENCODING=utf-8 python xxx.py


## developing

测试分级:
- 默认: 无须环境也无须很多时间. python -m pytest 运行。记得将所有.py用__name__保护，避免pytest发现用例时运行代码
- slow: 慢测试（RAG 模型加载 / 真实 comfy 出图 / 真实数据操作）。默认跳过，用 `python -m pytest -m slow` 运行
- once: 手动临时测试（一次性验证用）。默认跳过，用 `python -m pytest -m once` 运行

ruff: remember `python -m ruff check ./entropy`
