---
name: free-explore
description: 定义了对于非artist标签的探索的探索的系统性的方法论。
---

## 基础知识
中心思想: 主要探索artist以外的tag，生成用户更加满意的图片。

思路：
- 外貌
  - 服装
  - 饰品
- 动作
- 神态
- 环境
  - 场景
  - 天气
- 不限于此，发挥你的想象力


## 前置澄清
<ask-user
    need-user-confirmation="force"
    max-questions-per-time="3">
1. 前置依赖: skill:episode; 也别忘了episode skill中需要用户确认的

2. 简单确认参数
如果用户未明确以下事项，请向务必向用户显式提问，确认清楚后，才开始流程
- prompt数量 (默认下表，但需询问用户是否需要更多)
- 记得告知：这几个计划的timestep的type都是free, 而非artist_only 的
- 每一个prompt每次新增的tag数量不能超过 15 个（告知用户：推荐15个） 

（2.和3.必须分开回答）

3. 确认探索方向（直到用户让你别问了，就可以正式工作了）
- 采用下文提到的 grilling-style, 和用户讨论探索的方向。直到和用户达成一致
  - 对于每一种维度，你都给用户几个备选的（用自然语言），看看用户的反馈。建议提3-5次问答。
  - 你也可以在这个流程中，初步搞清楚用户的偏好、深度广度偏好

</ask-user>


## 正式流程

| 持续timestep个数 | 思路                              | prompt数量 per timestep | 备注 |
| ------------ | ------------------------------- | --------------------- | -- |
| N            | 与用户讨论更改方向，或者接受用户的反馈，想出新的prompt。记得查 entropy/conf/tag_datasets/danbooru.txt 找tag | 8                     | \- |

注意事项：

when: 添加tag前; do: 每一个prompt每次新增的tag数量不能超过15个; do_not: 新增很多很多tag; reason: 因为步子太大会造成不可观测（方差大）。删除不受影响;

when: 用户说 报错invalid tag过多; do: 情况一:报错信息中存在对标准tag的关联推荐，则在这里面找替代品。情况二:无推荐，则去 entropy/conf/tag_datasets/danbooru.txt 中寻找tag。注意：不需要把非标准tag清零，报错中的budget是容忍上限，预算内保留少量非标准tag可以提升表现力，优先替换可有可无的tag、保留表达关键特征的tag; do_not: -; reason: 报错信息中推荐的相关tag（如果有）是基于语义进行的RAG，比按关键词查准确。当然，前提是用户预先进行了RAG配置。;

when: 修复invalid tag; do: 将整个timestep进行全量替换效率最高; do_not: 编辑文件，或者分多次编辑；; reason: 编辑文件不如全量替换；多次编辑更差效率太低;

when: 发现想要的tag不存在时; do: 更换更简短的关键词，或者灵活变通，使用相近的替代; do_not: -; reason: 甚至可以使用不相近的替代：万一用户满意呢？;

when: 添加tag时; do: 合理组织探索维度，可进行交叉。例如prompt0探索衣服A+环境X，prompt1探索衣服B+动作Q+环境Y; do_not: 一个prompt只探索一个维度; reason: 用户对于每一种维度，都会进行反馈;

不要怀疑用户的prompt，默认用户给的prompt中的所有tag都有效。



## references
### grilling-style
```
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking

Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding.
```