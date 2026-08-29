---
name: setup-app-config
description: 配置 entropy/conf/app_config.yaml（从模板复制、填写 ComfyUI 地址等）。首次安装或 ComfyUI 端口变化时使用。当用户提到 setup-app-config 或"配置 app_config"时使用。
---

## 目标

生成或更新 `entropy/conf/app_config.yaml`。

所有配置字段的自解释说明见 `entropy/conf/app_config.example.yaml` 内注释，本 skill 不重复。

## 流程

### 1. 分支: app_config.yaml 是否已存在

- 不存在: 复制 `entropy/conf/app_config.example.yaml` → `entropy/conf/app_config.yaml`，继续第 2 步
- 已存在: 询问用户本次要修改什么（常见场景是 ComfyUI 端口变化 → 只改 `comfyui_base_url`），编辑对应字段后直接跳到收尾。不要覆盖已有配置

### 2. 询问用户

<ask-user need-user-confirmation="force" max-questions-per-time="2">
1. ComfyUI 服务地址是多少？（ComfyUI 跑在本机默认端口则保持 http://127.0.0.1:8188）
2. 是否需要"额外的有效 tag 白名单"文件？（可选，默认不需要；需要则创建文本文件并把路径填入 `extra_valid_tag_file`，用途见 example 注释）
</ask-user>

### 3. 填写

按回答编辑 `app_config.yaml` 对应字段（`comfyui_base_url` / `extra_valid_tag_file`），其余字段保持默认。

### 4. 收尾

- 通知用户: web 服务端口为 `port` 字段值（默认 5000），启动后浏览器访问 http://127.0.0.1:<port>
- 告知: 所有配置热加载，修改立即生效，无需重启
- 若本次是新建配置（而非修改已有配置）: 引导下一步执行 adapt-workflow skill 适配工作流
