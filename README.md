# ImageAutoPrompt

为 noobai / anima 模型创作 danbooru tag prompt 的探索工具。全程通过 coding agent（claude code / opencode 等）使用：复制下面的指令文本给 agent 即可，每条指令旁附 skill 链接供人类阅读。

## 安装

1. 安装 python 环境（[install-environment](.agents/skills/install-environment/SKILL.md)）:

   > 帮我使用 install-environment skill，安装环境

2. 配置 app_config.yaml（首次安装，或 ComfyUI 端口变化时）（[setup-app-config](.agents/skills/setup-app-config/SKILL.md)）:

   > 帮我使用 setup-app-config skill

3. 适配工作流（首次安装，或加入新工作流时）（[adapt-workflow](.agents/skills/adapt-workflow/SKILL.md)）:

   > 我想加入新的 Workflow 到 entropy/conf/workflows，帮我使用 adapt-workflow 将我的 Workflow 进行修改，我将它下载下来了，文件地址是：___

4. 启动服务（唯一需要手动运行的命令）:

   ```
   uv run server.py    # uv 路线
   python server.py    # python 环境
   ```

## 日常使用

探索画师串:

> 在新 episode 中，帮我使用 artist-explore 探索 artist. prompt: 1girl, solo, ...

不探索画师串，探索其他 tag:

> 在新 episode 中，帮我使用 free-explore 探索 free. prompt: 1girl, solo, ...

（关键问题都已内置到 skill 里，agent 会先与你确认，达成一致后开工）

## 进阶: RAG（可选）

RAG 提供 tag 灵感与纠错。安装 RAG 依赖与建库: [docs/install-rag.md](docs/install-rag.md)

内部实现: 阅读 AGENTS.md 与 .agents/skills/
