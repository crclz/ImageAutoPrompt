---
name: adapt-workflow
description: 将用户的 ComfyUI 工作流 json 适配本工具（插入占位符）并放入 entropy/conf/workflows/。当用户要加入或适配新工作流时使用。
---

## 目标

用户的工作流（ComfyUI 导出(API) 的 json）被放入 `entropy/conf/workflows/` 并插入占位符，随后可被 web 端创建 episode 时选用。

## 背景

- 本工具通过字符串替换向工作流注入内容，渲染逻辑见 `entropy/infra/comfy_api.py` 的 `render_workflow`
- 目标形态参考 `entropy/conf/workflows/workflow.example.json`（占位符用法的真实示例，直接读它理解，无需更多文档）
- 占位符: `entropy:positive`（必填，正向提示词）、`entropy:output_image`（必填，输出文件前缀，用于定位输出与防缓存）；`entropy:negative`、`entropy:lora`（可选，很少使用）
- 替换是"裸 token + JSON 转义注入"，因此占位符可整串独立（`"entropy:positive"`），也可子串混排（`"entropy:positive, masterpiece, best quality"`）
- 负向提示词节点通常固定为模型所需负词，不插占位符（本工具不探索负向词）

## 流程

### 1. 获取工作流文件

用户指令中应给出文件地址（ComfyUI 导出(API) 的下载件）；未给出则询问。通读 json，对照 `workflow.example.json` 理解节点结构与目标形态。

### 2. 修改

- 将文件复制为 `entropy/conf/workflows/<合适的名字>.json`，在副本上修改（不动用户的原始文件）
- 插入占位符，完成适配

### 3. 歧义时确认

<ask-user need-user-confirmation="force">
出现以下情况时，先向用户展示你的理解并列出疑点，确认后再动手:
- 存在多个正向文本节点，无法确定注入点
- 图片输出节点不明确或存在多个
- 工作流结构与 example 差异过大
</ask-user>

### 4. 收尾

- 告知用户: 工作流已入库，web 端创建 episode 的下拉框即可看到（CLI 用 `python entropy/cli/discover_workflows.py` 列出）
- 提示: 创建 episode 时所选工作流会快照进 episode.json，之后改文件不影响已有 episode
