---
name: episode
description: 一个episode代表了对prompt进行优化的轨迹。本skill涉及：episode的文件格式、流程。
---

## 简介
一个episode代表了对prompt进行优化的轨迹。

## prompt 格式

一个prompt分为两部分: 正向提示词、负向提示词。
```
positive
<positive>

negative
null
```

为什么不需要negative？因为用户已经按照自己审美积累了负向提示词，并已集成到后续的流程。你无需生成任何negative。
从经验来看，对于画面的把控与调整，也需要靠正面提示词。



## episode
对于一个prompt的探索，都是属于同一个episode。你需要让用户决定episode该叫什么名字，需要符合编程语言的identifier命名规则，且必须是snake_case，且不能中文.

runs/draft/episode_name 是一个文件夹。


## timestep

episode由多个timestep组成。

| 动作                                            | 备注                                                                  |
| --------------------------------------------- | ------------------------------------------------------------------- |
| 1.  基于之前的prompt，以及用户的反馈，生成新timestep，并存放到磁盘文件。 | 需根据用户的反馈，仔细思考新的timestep。注意平衡exploration和exploitation                |
| 2.  告诉用户文件相对地址，用户自己会跑文生图         | 注意前后需要空格且冒号用英文不然跳转卡手. 文件地址: xxx.md |
| 3.  用户会给出反馈                                   | \-                                                                  |
| 4.  你开启下一个timestep，回到 1                       | \-                                                                  |

## timestep文件

runs/draft/episode_name/timestep_i.md 其中i从0开始. i建议长度为2, 例如05, 10

timestep_i.md 的格式如下:

```timestep_i.md
<exploration>
输出exploration代码块
</exploration>

<prompts>
N个，按下文格式。从prompt0开始的代码块。以及i_relative_
</prompts>
```

exploration代码块（需带```exploration）
```exploration
{
    "type": string, // "artist_only", "free". 
    "description": string, // 讲一讲探索的方向. 30字以内
    "keywords": List[string], // 长度为3-5，用中文描述一下探索的关键词
    "format_reminder_constant": {
        "tag_style": string, // "space=yes underscore=no", "space=no underscore=yes"
    }
}
```

artist_only 时，只能修改artist，不能修改其他。
free时，可以修改其他。

format_reminder_constant: 常量，所有episode固定，但你需每一个timestep重复输出，由文章开头部分的“prompt格式”决定。


输出prompt前，请思考一下artist tag应该放在哪个位置，免得放错。
prompts格式:


0_relative_diff_target: (简短描述该prompt与其他prompt的相对区别，让人无需读完每一个positive，就能知道该prompt的思路)
0_relative_diff_tag: (tag有哪些区别)

```prompt0
positive
<positive>

negative
null
```

...

3_relative_diff_target: (简短描述该prompt与其他prompt的相对区别，让人无需读完每一个positive，就能知道该prompt的思路)
3_relative_diff_tag: (tag有哪些区别)

```prompt3
positive
<positive>

negative
null
```


## Workflows

### 工作流通用规则

when: 没有episode_name; do: 需要用户想一个，或者帮用户想一个; do_not: 基于猜测，从已有的episode继续进行探索;

when: 生成timestep时; do: 一次只生成1个timestep; do_not: 一次多个;

when: timestep文件写入后; do: 告诉用户文件相对地址; do_not: 将timestep文件内容重复给用户;

when: 文生图命令失败; do: 根据报错信息，判断是不是md文件格式问题，如果是则修改；否则让用户处理; do_not: 试图处理不该由你处理的问题;



### workflow: free exploration
- 中心思想: 主要探索artist以外的tag，生成用户更加满意的图片。
  - 自然环境、社会环境
  - 外貌、语言、动作、心理、神态
  - 整体外貌、容貌五官、衣着服饰、姿态神情
  - 不限于此，发挥你的想象力

| 持续timestep个数 | 思路                              | prompt数量 per timestep | 备注 |
| ------------ | ------------------------------- | --------------------- | -- |
| N            | 与用户讨论更改方向，或者接受用户的反馈，想出新的prompt。 | 8                     | \- |

注意事项：

when: 添加tag前; do: 每一个prompt每次新增的tag数量不能超过10个; do_not: 新增很多很多tag; reason: 因为步子太大会造成不可观测（方差大）。删除不受影响;

when: 用户说 报错invalid tag过多; do: 情况一:报错信息中存在对标准tag的关联推荐，则在这里面找替代品。情况二:无推荐，则去 datasets/danbooru.txt 中寻找tag; do_not: -; reason: 报错信息中推荐的相关tag（如果有）是基于语义进行的RAG，比按关键词查准确。当然，前提是用户预先进行了RAG配置。;

when: 修复invalid tag; do: 将整个timestep进行全量替换效率最高; do_not: 编辑文件，或者分多次编辑；; reason: 编辑文件不如全量替换；多次编辑更差效率太低;

when: 发现想要的tag不存在时; do: 更换更简短的关键词，或者灵活变通，使用相近的替代; do_not: -; reason: 甚至可以使用不相近的替代：万一用户满意呢？;

when: 添加tag时; do: 合理组织探索维度，可进行交叉。例如prompt0探索衣服A+环境X，prompt1探索衣服B+动作Q+环境Y; do_not: 一个prompt只探索一个维度; reason: 用户对于每一种维度，都会进行反馈;