---
name: format-noobai
description: 定义了对于noobai的文生图prompt的格式标准。当需要生成完整prompt时需参考。
---

## 范围
适用于noobai系列

## 正向提示词
对于正向提示词，最佳实践比较建议按照以下格式。
```
`[人数tag 1girl, solo], [角色名 optional], [角色所属的作品系列名 optional], [画师tag artist:xxx], [一般tag: 动作/表情 服装/道具 背景描述 等等其他 都属于一般tag], [质量词]`
```

关于artist:

| example                                                                                          | reason                   |
| ------------------------------------------------------------------------------------------------ | ------------------------ |
| 1girl, solo, artist:xx1, artist:xx2, light, smile, white dress, garden, flowers, wind, long hair | 无角色名和系列名，artist 直接置于人数后  |
| 1girl, solo, artoria pendragon, fate stay night, (artist:asd:0.8), armor, sword                  | 有角色名称、有系列名称。权重需括号        |
| `1girl, solo, artoria pendragon, artist:some \(one\), armor, sword`                              | 必须使用完整 artist。如果有括号，需转义。 |


关于tag:
when: 设置negative prompt时; do: 包含negative关键字 且下方保持null; do_not: -; reason: 格式要求;

when: 考虑添加质量词时; do: 不添加任何质量词，例如masterpiece, best quality,newest,absurdres; do_not: -; reason: 用户已预置;

when: 使用画师标签时; do: 画师必须添加 artist: 前缀; do_not: -; reason: noobai要求;

when: 确定画师标签位置时; do: 将画师置于正确的位置，如上表所示。在生成 prompt 前，思考画师标签插入的位置。; do_not: 将画师置于末尾; reason: 除了特殊的 tag，其他全都是一般 tag;

when: 为标签添加权重时; do: 为artist添加权重以精调画风 且权重记得添加括号例如(artist:xxx:1.1); do_not: 为其他tag添加权重; reason: 为了稳定性，不能为artist以外的tag添加权重，除非用户要求;

when: 确定标签编写风格时; do: 采用标准的danbooru tag; do_not: 采用自然语言; reason: 对齐到训练数据;

when: 编写包含多个单词的tag时; do: medium breasts; do_not: medium_breasts; reason: tag下划线换成空格;

when: 编写包含括号的标签时; do: `lumine \(genshin impact\)`; do_not: `lumine_(genshin_impact)`; reason: noobai任何标签自带的括号需转义;

when: 控制标签总数时; do: 正向tag低于80个; do_not: 正向tag超过100个; reason: 根据经验 80以内最优;