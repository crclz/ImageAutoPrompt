---
name: artists-clustering
description: 画师串进行分簇
disable-model-invocation: true
---

1. 将画师串分成N个簇（按直觉看看亲缘关系）
2. 最终输出 24 个不同的画师串。优先选择不同的簇（为了保证多样性）。簇内随机选择。
```
1: (artist:xxx), (artist:xxx)
2:...
24: ...
```
