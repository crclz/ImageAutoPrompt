# ImageAutoPrompt

## 安装
1. 安装基础功能: [docs/install-basic.md](docs/install-basic.md)
   - [BV1L7RcBAEqN](https://www.bilibili.com/video/BV1L7RcBAEqN)
2. 安装RAG功能: [docs/install-rag.md](docs/install-rag.md)
3. 其他未提到的选项，如果有疑问，可以看老readme: [docs/README-old.md](docs/README-old.md)


## 主要功能

1. 使用 claude code / opencode 探索画师串
   - 依赖：安装基础功能
2. 使用 claude code / opencode 探索其他 tag
   - 依赖：安装基础功能
   - 有rag会更好（依赖：安装RAG功能）

内部实现：阅读 AGENTS.md 和 .agents/skills


## 用法
(关键问题都已经内置到skill里，agent会前置向用户确认一些关键问题。达成一致后才会开工)

探索画师串:
```
帮我探索artist. prompt: 1girl, solo, ...
```

不探索画师串，探索其他的tag:

```
帮我探索free. prompt: 1girl, solo, ...
```
