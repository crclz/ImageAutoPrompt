---
name: format-anima
description: 定义了对于anima的文生图prompt的格式标准。当需要生成完整prompt时需参考。
---

## 范围
适用于anima的 Turbo 与 Base 系列。
版本差异：Base 是未精调的基础模型，默认风格朴素，更依赖 artist 标签与质量词；Turbo 是蒸馏版，更稳定。
文本编码器为 Qwen3-0.6B（LLM）：无 CLIP 77-token 截断，长 prompt 可完整编码；NL 理解能力有限（0.6B 小模型）。

## 正向提示词
对于正向提示词，最佳实践比较建议按照以下格式。
```
`[人数tag 1girl, solo], [角色名 optional], [角色所属的作品系列名 optional], [@画师tag optional], [一般tag: 主体动作/表情 → 细节(五官/发型/服装/道具) → 氛围(光线/背景/景深) → 情绪收尾(dreamy, elegant 等)]`
```
注意：质量词（masterpiece, best quality, very aesthetic, score_9, score_8, absurdres 等）、safety 标签（safe/nsfw 等）、year/meta 标签（year 2025, newest 等）均由工作流预置在 prompt 最前，agent 不添加。
注意：prompt 过短或缺细节时，模型易产生意外结果和不期望内容（官方指引），应保持详实。

关于artist:

| example                                                                                          | reason                   |
| ------------------------------------------------------------------------------------------------ | ------------------------ |
| 1girl, solo, @nnn yryr, smile, brown hair, hat, solo, ...                                        | 无角色名和系列名，artist 直接置于人数后  |
| 1girl, solo, oomuro sakurako, yuru yuri, (@nnn yryr:1.3), smile, ...                             | 有角色名称、有系列名称。权重需括号        |
| `1girl, solo, @scottie \(phantom2\), armor, sword`                                               | 画师名自带括号需转义。 |

关于tag:
when: 设置negative prompt时; do: 不添加任何内容; do_not: -; reason: 工作流已预置官方推荐负向词（worst quality, low quality, score_1, score_2, score_3, artist name, blurry 等）;

when: 考虑添加质量词时; do: 不添加任何质量词; do_not: -; reason: 工作流已预置（score_9, score_8, amazing quality, very aesthetic, absurdres）;

when: 使用画师标签时; do: 画师必须添加 @ 前缀; do_not: -; reason: anima要求，不加@效果很弱;

when: 确定画师标签位置时; do: 将画师置于正确的位置，如上表所示。在生成 prompt 前，思考画师标签插入的位置。; do_not: 将画师置于末尾; reason: 除了特殊的 tag，其他全都是一般 tag;

when: 为标签添加权重时; do: 仅artist可加权，格式 (@artist名:权重)，权重范围0.5-1.5，步进0.1; do_not: 为其他tag添加权重; reason: 稳定性考虑，（主导画师取高值，副画师取低值）;

when: 确定标签编写风格时; do: 采用标准的danbooru tag，或按官方指引混合自然语言（见下节）; do_not: -; reason: 对齐到训练数据;

when: 标准tag无法表达颜色、材质等属性组合时; do: tag中心词 + 修饰短语块，如 red and green striped cowboy hat; do_not: 改写成完整句子; reason: anima具备有限的NL理解，能解析以tag为锚点的短修饰串，详见「推荐风格」节;

when: 需要表达概念间关系（持物、位置、动作）时; do: 关系短语块，如 holding bubble tea against chest; do_not: 只罗列孤立tag; reason: 孤立tag无法绑定手、物、位置的对应关系;

when: 该概念已有标准tag时; do: 优先用标准tag，如 one eye closed，短语块仅作补充; do_not: 用短语块复述标准tag能表达的概念; reason: 标准tag与训练分布对齐，触发最稳定;

when: 编写包含多个单词的tag时; do: medium breasts; do_not: medium_breasts; reason: tag下划线换成空格，score tag（score_7）是唯一例外;

when: 编写包含括号的标签时; do: `keqing \(genshin impact\)`; do_not: 不转义; reason: anima实测仍需转义;

## 自然语言混合（官方推荐）
注意：官方允许混合 ≠ 本仓库默认写法，默认采用「tag骨架 + 短语块」风格（见下节）。
- tag 与自然语言可任意顺序混合。
- 纯自然语言时至少2句话，越详细越好；过短易出意外结果。
- 角色名与系列名使用标准英文大小写。
- 质量/artist tag 可置于自然语言开头，例如 "masterpiece, best quality, @big chungus. An anime girl with medium-length blonde hair is..."
- 多角色场景：先报角色名，再描述其外貌，避免模型混淆。
- 数据集tag（高级特性）：ye-pop / deviantart 开头 + 换行 + 作品描述，可提升风格与内容多样性。

## 推荐风格：tag骨架 + 短语块（本仓库默认）
从完全自然语言到完全danbooru tag是一条光谱：

| 档 | 名称 | 形态 |
| --- | --- | --- |
| A | 叙事自然语言 | 完整句子，可成段 |
| B | 短语流自然语言 | 逗号分隔的流畅描述短语（5~15词），含情绪叙事与meta评论 |
| C | tag骨架 + 短语块 | 标准tag打底，挂2~6词的短语碎块表达无tag载体的概念 |
| D | 纯danbooru tag | 只用受控词表 |

本仓库默认 C 档：标准tag承担骨架（人数、构图、人物属性、场景实体），短语块承担标准tag覆盖不到的属性组合与概念间关系。追求最大可控性（如单变量消融实验）时可退到 D 档。

### 书写规则
- 碎块读起来别是一整句话；推荐单个碎块 ≤6 词左右
- 禁叙事/meta层：不写情绪评论（emotionally moving）、故事句（as if she has just turned around...）、收尾感叹（a scene that invites the viewer）。原因：anima 对叙事NL理解弱，此类内容不落图，应转化为可见特征
- 禁否定式定向：不用 not aggressive 之类的否定描述，改写为正向短语（calm expression）或进 negative

### 示例片段
颜色材质修饰（tag中心词 + 修饰串）:
- red and green striped cowboy hat
- gown woven from starlight and liquid moonlight
- pastel blue trim on bikini

动作与位置关系（概念间绑定）:
- one hand holding graduation certificate against chest, other hand in own hair
- holding bubble tea against chest, sipping from straw
- petals drifting across foreground, out of focus petals

光源绑定（效果绑定到源）:
- eye reflection of fireworks
- rim lighting on hair and shoulders
- sunlight through loose strands

数量与程度:
- a few soft petals
- enormous glowing moons
- huge moon behind her

取景装置:
- sniper scope, view through circular scope
- blurred darkened scope edges, lens reflection

氛围收尾:
- dreamy blue purple night atmosphere
- nostalgic spring atmosphere

### 完整示例
基础形态（泳池少女）:
```
1girl, solo, standing, cowboy shot, looking at viewer, light smile, blush,
aqua eyes, detailed eyes, long eyelashes, glossy lips, eye reflection of sunlight and water,
silver hair, long hair, wet hair, floating hair, wind, sunlight through loose strands,
hand in own hair, brushing damp hair behind ear, relaxed posture,
bare shoulders, collarbone, navel, wet skin, water drop on skin, sunlight refraction on water drops,
white bikini, pastel blue trim on bikini,
poolside, pool, clear water, water reflection of sky and clouds, flower petals floating on water surface,
blue sky, clouds, summer, gentle summer atmosphere,
blurry background, depth of field, bokeh, soft cinematic lighting, summer glow
```

带角色名与取景装置（初音·狙击镜）:
```
1girl, solo, hatsune miku, vocaloid,
sniper scope, view through circular scope, crosshair, vignette, blurred darkened scope edges, lens reflection,
close-up, upper body, unfocused eyes, melancholic expression, long eyelashes, detailed eyes, glossy lips,
eye reflection of fireworks, colored light reflecting on eyes and hair,
twintails, long hair, aqua hair, aqua eyes, floating hair, wind,
classic miku outfit, detached sleeves, realistic fabric folds, holding cold drink against chest,
night, night sky, distant fireworks, light particles, summer,
dreamy blue purple night atmosphere, soft atmospheric lighting, depth of field
```

材质与关系的极限案例（星空礼服）:
```
1girl, solo, cowboy shot, looking at viewer, gentle gaze, parted lips, blush,
blue eyes, detailed eyes, long eyelashes, glossy lips, eye reflection of stars and moonlight,
platinum blonde hair, long hair, hair over shoulder, moonlight on loose strands,
evening gown, dark blue dress, off shoulder, collarbone, cleavage,
gown woven from starlight and liquid moonlight, tiny constellations shimmering in fabric, layered translucent silk,
one hand gathering dress at waist, other hand on own chest,
night, night sky, starry sky, floating stars, glowing flower petals,
full moon, huge moon behind her, distant galaxies reflected like water, soft light ribbons drifting in air,
moonlight, rim lighting on hair and shoulders, depth of field, dreamlike fantasy atmosphere
```

## tag 参考
tag 参考来源：entropy/conf/tag_datasets/danbooru.txt（本仓库数据集）
