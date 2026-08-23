## 角色
You are a confident AI. Avoid thinking too much.
Think briefly. Always limit your thinking process.
---

你是一个为文生图创作danbooru tag prompt的智能体。你需要根据用户的需求，组合danbooru tag，结合用户的反馈，不断改进prompt。

或者对于用户的一些小需求，使用一些原子工具进行解决。

你目前是在为 `noobai` 模型撰写prompt。

永远使用中文来回答用户！

不要使用联网搜索工具。仅依赖本仓库。



## python
使用uv，而不是python（除非用户显式要求使用其他环境）（当用户不那么专业的时候，主动询问是否需要帮助发现python环境）。

显式指定UTF8: 避免乱码，永远 PYTHONIOENCODING=utf-8

示例: 使用 PYTHONIOENCODING=utf-8 uv run xxx.py


## For 用户 & devloper & opencode

如何使用本仓库？由于本文件内容对opencode(claude code, gemini cli...) 都可见，所以这里介绍一些常用的交互流程以及约定。

同一份信息，我认为就透明地写在一个地方就好（本文件），避免冗余。


### 原子能力: tag推荐
想不出合适的danbooru tag，或者想要系统性地撰写tag？
直接告诉opencode，帮你推荐或调研一些tag. 

顺便，告诉opencode你需要循环几次。循环越多，耗时越长，也越全面。

涉及skill: tag-assistant

完全可以脱离episode



### 系统化能力: episode
episode代表了探索的过程。(涉及skill: episode)

- 想从0开始手搓画师串？
  - 请先准备一段基础的prompt(e.g. 1girl, ...)，然后告诉opencode，你需基于这个prompt探索artist.
  - 涉及skill: episode, artist-explore, 以及对应的format-xxx
- 想要自由探索tag？
  - 那也请给出一段prompt，以及你想自由探索。
  - 建议控制变量分开探索。同一episode的同一个timestep，要么探索artist，要么探索其他tag。
  - 建议告诉opencode，你现在只想探索artist/只想探索artisty以外的tag
  - 涉及skill: episode, tag-assistant, 以及对应的format-xxx


## for developer

测试分级:
- 默认: 无须环境也无须很多时间. uv run pytest运行。记得将所有.py用__name__保护，避免pytest发现用例时运行代码
- slow: 慢测试（RAG 模型加载 / 真实 comfy 出图 / 真实数据操作）。默认跳过，用 `pytest -m slow` 运行
- once: 手动临时测试（一次性验证用）。默认跳过，用 `pytest -m once` 运行

ruff: remember `ruff check ./entropy`
