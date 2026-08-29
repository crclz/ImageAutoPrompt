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

episode 通过 CLI 创建:

```
uv run entropy/cli/create_episode.py --name {episode_name}
```

极其少数情况下需要回看整个 episode 的历史轨迹（各 timestep 的 prompt、反馈等）时，执行 `uv run entropy/cli/get_trajectory.py --episode {episode_name}` 获取 episode.json 的绝对路径，自行阅读分析（只读，勿编辑）。



## timestep

episode由多个timestep组成。

| 动作                                            | 备注                                                                  |
| --------------------------------------------- | ------------------------------------------------------------------- |
| 1.  基于之前的prompt，以及用户的反馈，生成新timestep，写入当前目录的 {episode_name}.{rand}.new_timestep.draft.md（{rand}为随机后缀，见「timestep文件」节）。 | 需根据用户的反馈，仔细思考新的timestep。注意平衡exploration和exploitation                |
| 2.  执行 `uv run entropy/cli/run_timestep.py --name {episode_name} --draft {episode_name}.{rand}.new_timestep.draft.md` 跑文生图。 | 新episode需先用 entropy/cli/create_episode.py 创建。命令耗时较长（出图慢），请将命令超时设置为10分钟以上，然后直接同步等待命令跑完。文件地址告知用户只是顺带 |
| 3.  用户会在网页端标记高分图片，并告诉你。你用 `uv run entropy/cli/get_feedback.py --name {episode_name}` 获取反馈。 | 默认取最新timestep；`--timestep i` 可指定（绝大部分情况不用传）。若反馈与上次相同（没变），停止并向用户二次确认 |
| 4.  你开启下一个timestep，回到 1                       | \-                                                                  |


## timestep文件

draft 文件放在当前目录，命名为 {episode_name}.{rand}.new_timestep.draft.md（例如 hello.7k2f.new_timestep.draft.md）。{rand} 是每次生成的随机数字/字母后缀（2-4位）。每个timestep都使用全新的随机后缀：文件名不与残留的旧 draft 冲突，可避免某些 harness 对覆盖已存在文件的「写前必读」限制带来的失败和浪费。（运行成功后文件会被移动到 episode 目录存档）

{episode_name}.{rand}.new_timestep.draft.md 的示例如下（不包含begin/end）

begin {episode_name}.{rand}.new_timestep.draft.md

<exploration>
{
    "type": string, // "artist_only", "lora_only", "free". 
    "description": string, // 讲一讲探索的方向. 30字以内
    "keywords": List[string], // 长度为3-5，用中文描述一下探索的关键词
    "format_reminder_constant": {
        "tag_style": string, // "space=yes underscore=no", "space=no underscore=yes"
    }
}
</exploration>

<prompts>
0_relative_diff_target: (简短描述该prompt与其他prompt的相对区别，让人无需读完每一个positive，就能知道该prompt的思路)
0_relative_diff_tag: (tag有哪些区别)

```prompt0
positive
<positive>

negative
null

lora
<lora:xxx:1.0> <lora:yyy:0.9>
```

lora 部分是可选的：有 lora 就写 `lora` 行 + 对应的 `<lora:name:weight>` 列表；没有 lora 时，`lora` 行整段去掉。

...

3_relative_diff_target: (简短描述该prompt与其他prompt的相对区别，让人无需读完每一个positive，就能知道该prompt的思路)
3_relative_diff_tag: (tag有哪些区别)

```prompt3
positive
<positive>

negative
null
```
</prompts>

end

注意

artist_only 时，只能修改artist，不能修改其他。
lora_only 时，只能修改lora，不能修改其他。
free时，可以修改其他。

format_reminder_constant: 常量，所有episode固定，但你需每一个timestep重复输出，由文章开头部分的“prompt格式”决定。

输出prompt前，请思考一下artist/lora tag应该放在哪个位置，免得放错。


## 前置澄清
前置依赖: skill:episode

如果用户未明确以下事项，请向务必向用户显式提问，确认清楚后，才开始流程

- episode_name: 是新建，还是沿用现有？如果是新建，则帮用户想一个，但是得用户确认
- 进行的工作流的种类: 是artist(对应skill: artist-explore)，lora(对应skill: lora-explore)，还是free(对应skill: free-explore)
- 目标模型（anima / noobai）：决定采用 format-anima 还是 format-noobai


## 工作流通用规则

when: 没有episode_name; do: 需要用户想一个，或者帮用户想一个; do_not: 基于猜测，从已有的episode继续进行探索;

when: 生成timestep时; do: 一次只生成1个timestep; do_not: 一次多个;

when: timestep文件写入后; do: 执行 entropy/cli/run_timestep.py 跑文生图（文件地址告知用户只是顺带）; do_not: 将timestep文件内容重复给用户;

when: 执行 run_timestep 时; do: 将命令超时设置为10分钟以上（出图耗时较长），然后直接同步等待命令完成; do_not: 使用默认短超时导致命令被中断; do_not: 放到后台异步运行、再轮询检测进度——没有必要，同步等待即可;

when: 获取用户反馈; do: 执行 `uv run entropy/cli/get_feedback.py --name {episode_name}`（不带 --timestep）；若反馈与上次相同，停止并向用户二次确认; do_not: 基于猜测代替用户评价;

when: 文生图命令失败; do: 根据报错信息，判断是不是md文件格式问题，如果是则修改draft后重新执行；若报错提示invalid tag超预算（见budget），按提示把无效tag压回预算内（保留表达关键特征的tag，替换可有可无的，不必清零）；否则让用户处理; do_not: 试图处理不该由你处理的问题;

