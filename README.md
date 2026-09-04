# ImageAutoPrompt

为 noobai / anima 模型创作 danbooru tag prompt 的探索工具。全程通过 coding agent（claude code / opencode 等）使用：复制下面的指令文本给 agent 即可，每条指令旁附 skill 链接供人类阅读。

## 前置要求
- 你有自己的comfyui工作流（本仓库并不指导安装comfyui）


## 功能
**核心功能**

本仓库主打的功能是episode，即对一个prompt进行不断的跑图-反馈-再跑图的循环。

探索画师串:

> 在新 episode 中，帮我使用 artist-explore 探索 artist. prompt: 1girl, solo, ...

不探索画师串，探索其他 tag:

> 在新 episode 中，帮我使用 free-explore 探索 free. prompt: 1girl, solo, ...

（关键问题都已内置到 skill 里，agent 会先与你确认，达成一致后开工）

**其他功能**

prompt编写原子工具
> 帮我使用 format-anima skill 编写prompt. <粘贴多模态图片> <或者粘贴图片描述> 

artist-name-search
> 帮我使用 artist-name-search 找一找 pixiv的画师 (https://www.pixiv.net/users/1554775) 的danbooru tag是什么?

> 帮我使用 artist-name-search 找一找 danbooru=yoneyama_mai的画师，pixiv是什么？

lora搜索
> 帮我使用 civitai-lora-search 搜索画师xxx的、适合于noobai的lora


## 环境安装

1. 安装 python 环境（[install-environment](.agents/skills/install-environment/SKILL.md)）:

   > 帮我使用 install-environment skill，安装环境

2. 配置 app_config.yaml（首次安装，或 ComfyUI 端口变化时）（[setup-app-config](.agents/skills/setup-app-config/SKILL.md)）:

   > 帮我使用 setup-app-config skill

3. 适配工作流（首次安装，或加入新工作流时）（[adapt-workflow](.agents/skills/adapt-workflow/SKILL.md)）:
   - 先在comfyui工作流顶部标签 - 右键 - 导出 API

   > 我想加入新的 Workflow 到 entropy/conf/workflows，帮我使用 adapt-workflow 将我的 Workflow 进行修改，我将它下载下来了，文件地址是：___

4. 启动服务（唯一需要手动运行的命令）:

   ```
   python server.py
   ```



## 进阶: RAG（可选）

RAG 提供 tag 灵感与纠错。安装 RAG 依赖与建库: [docs/install-rag.md](docs/install-rag.md)

内部实现: 阅读 AGENTS.md 与 .agents/skills/
