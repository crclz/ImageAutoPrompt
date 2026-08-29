---
name: artist-explore
description: 定义了对于artist(aka画风 画师串)的探索的系统性的方法论。适用于anima与noobai
---

## 画师(artist)

本skill适用于 anima 与 noobai，方法论两模型通用；画师tag的写法因模型而异，见下方「模型差异对照」。画师两模型共用。

对于画师（画风），从经验来看，单画师的作用有限，需要叠加多名画师（aka画师串）。

一般来说，一个好的画师串由2-5名画师组成，需要不断探索，不断试错。

另外，有一个高级技巧，能更精细化组合画师，将tag括号括起来并添加权重。权重属于高级技巧，不要一上来就用。

### 模型差异对照

| 模型 | 画师tag前缀 | 无权重写法 | 权重写法 | 权重范围 |
| ---- | ----------- | ---------- | -------- | -------- |
| noobai | `artist:` | `artist:aaa, artist:bbb` | `(artist:aaa:0.9)` | 0.5-1.0闭区间，step 0.1 |
| anima | `@` | `@aaa, @bbb` | `(@aaa:0.9)` | 0.5-1.5，step 0.1 |

两模型通用：
- 画师名自带括号需转义，如 `artist:scottie \(phantom2\)` / `@scottie \(phantom2\)`
- 画师tag置于人数tag（及角色名/系列名，若有）之后，不放末尾
- 仅画师tag可加权，不为其他tag加权


## workflow: artist exploration and exploitation
中心思想：从无artist或者指定的artist开始，从简单到复杂：先尝试少量画师无权重组合，逐步复杂化，途中根据用户的反馈，调整画师组合。最终得到最优画师组合。

### 前置澄清
<ask-user
    need-user-confirmation="force"
    max-questions-per-time="3">

如果用户未明确以下事项，请向务必向用户显式提问，确认清楚后，才开始流程
- 前置依赖: skill:episode; 也别忘了episode skill中需要用户确认的
- 目标模型（anima / noobai），决定画师tag写法，见「模型差异对照」
- dropout比例 (默认推荐0.5). dropout功能的含义是在每一episode开始时，dropout掉一部分artist，以避免与之前的episode选到过于相似的artist。
- prompt数量 (默认下表，但需询问用户显式确认是否需要更多)
- 执行计划（简要说明即可）。记得告知（而非询问），这几个计划的timestep都是 artist_only 的

</ask-user>

### 流程
注意:
- 探索artist时，为了控制变量，我们不修改其他标签。这是为了确保图片效果的改善都是因为artist。
- 注意正确的artist tag的插入位置


| 持续timestep个数 | 思路                                                          | prompt数量 per timestep | 备注                                                    |
| ------------ | ----------------------------------------------------------- | --------------------- | ----------------------------------------------------- |
| -            | 获取artist. 运行 get_artists.py。后续的artist只能从这里面选择 | -                    |  - |
| 1            | 进行单画师探索。基于上一步的输出，然后选择你认为适合的画师，不能重复。 | 16                    | artist_only；如果用户无明显停留意图，你需要主动推进到下一个阶段。                |
| 1            | 2画师无权重混合。不要用上一阶段用户完全未看过的。重点关注用户在单artist阶段更喜欢的。              | 8                     | 同上                                                    |
| 1            | 23画师带权重.                                                    | 8                     | 同上；注意一般1画师没有2画师好，但是再往上就没这个规律，得试错。                     |
| 2            | 2345画师带权重                                                   | 8                     | 同上；注意最后一个timestep需平衡exploration和exploitation。前3名都很重要。 |
| 0            | 得出结论，将最后一个timestep的前3个画师串告诉用户                               | \-                    | 如果用户想要进行其他探索，那你就轮换使用前3个画师串。                           |


## reference
在寻找artist的时候，请一定要通过 get_artists.py 获取候选artist，这是artist库的唯一出口；不要直接阅读artist库原始md文件。

运行方式（在仓库根目录执行）：
```bash
uv run .agents/skills/artist-explore/scripts/get_artists.py --dropout=0.3
```

--dropout 必传，取值 [0,1)，表示随机丢弃的artist比例。
