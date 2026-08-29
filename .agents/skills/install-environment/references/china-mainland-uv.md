# 中国大陆如何使用 uv

中国大陆使用 uv，面临以下问题：

- pypi 源下载慢：解决方案简单，但网上容易找到错误资料
- python 解释器下载慢：所需 python 版本本地没有时 uv 会自动下载解释器，默认源非常缓慢

## pypi 源

请认准官方文档: https://docs.astral.sh/uv/concepts/configuration-files/

首先，建立一个 `uv.toml` 文件，内容如下。注意第一行是 `[[index]]`，不是 `[[tool.uv.index]]`（后者是 pyproject.toml 里的写法）:

```toml
[[index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

然后，将 `uv.toml` 放到用户级配置位置，对你电脑上所有 uv 项目生效：

- Windows: `%APPDATA%\uv\uv.toml`
- Linux/macOS: `~/.config/uv/uv.toml`

注意：本仓库的 pyproject.toml 已将 torch 固定为 pytorch 官方 cu126 源（explicit index），上述镜像不影响 torch 的下载源，torch 仍从 pytorch 官方下载。

## python 解释器下载慢

在 `uv sync` 之前，先用镜像源预装解释器（uv 发现本地已有满足版本要求的解释器后，sync 时不会再下载）:

```bash
uv python install 3.12 --mirror=https://registry.npmmirror.com/-/binary/python-build-standalone/
```
