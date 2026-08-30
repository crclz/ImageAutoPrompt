# style_feature (画风维度短语库)

> 短语提炼自 `library/artists.md` 的画师分析与通用画风词汇，遇到新的画风描述可随手回填本库。

- 同组内短语可根据语义自由组合，是否冲突由语义判断
- 英文写入 prompt，中文仅作释义
- 描述性、氛围感的短语不必遵循 danbooru tag，也无需验证是否为有效 tag——danbooru 标注最缺少的正是这类难以定量评价的风格描述

### 1. 色彩 (color)
// 实测：色彩总体影响有限
// 实测：优先放到末尾，作为氛围
// TODO: 测测非turbo模型
- `warm colors` 温暖
- `cold colors` 冰冷
- `complementary colors, warm-cool contrast` 冷暖对比/补色碰撞
- `highly saturated` 浓艳
- `desaturated, muted colors` 灰调
- `morandi colors, muted gray palette` 莫兰迪/高级灰
- `bright and airy` 明亮通透
- `dark and gloomy` 昏暗
- `pastel colors` 粉彩
- `candy colors` 糖果色
- `macaron colors` 马卡龙色
- `pink and purple palette` 粉紫调
- `iridescent, aurora colors` 虹彩/极光/镭射
- `neon, fluorescent colors` 荧光色
- `cool background, warm skin` 冷背暖皮
- `monochrome, greyscale` 黑白
- `limited palette` 少色数
- `colorful, vibrant palette` 繁彩
- `faded retro colors` 复旧褪色
- `film-like tones` 胶片调

### 2. 光影 (light & shadow)
// 和色彩差不多的结论. 
- `soft diffused lighting` 柔和漫射光
- `harsh dramatic lighting` 硬光戏剧化
- `rim light` 轮廓光
- `backlighting` 逆光
- `tyndall effect, god rays` 丁达尔/体积光
- `lens flare` 镜头光晕
- `chromatic aberration, rgb shift` 色散
- `bloom, glowing light overflow` 辉光/溢光
- `bokeh` 焦外散景
- `soft focus` 柔焦
- `hard cel shading` 硬赛璐璐
- `soft gradient shading` 柔和渐变
- `painterly shadows` 厚涂式阴影
- `colored shadows` 彩色/环境色阴影
- `subsurface scattering` 次表面散射
- `ambient light, environmental color bleed` 环境光渗色
- `strong contrast, chiaroscuro` 强明暗对比
- `spotlight` 舞台聚光
- `light through blinds` 百叶窗切光
- `golden hour lighting` 黄昏光

// TODO: flower sea

1girl, solo, magical girl, cowboy shot, looking at viewer, light smile, blush, closed mouth, in flowers, in flower sea, flowers,
holding staff, clasping staff with both hands,
pink purple eyes, detailed eyes, jewel-like sparkle in eyes, long eyelashes,
blonde hair, very long hair, curly hair, gradient hair, soft pink gradient toward hair tips, ahoge, floating hair,
hair ornament, bow, crown, white cat ear shaped bow, golden feather crown with pink heart gem,
white dress, layered white and pink dress, frills, lace trim, gold trim on dress edges,
small golden feathered wings on shoulders, white ribbon collar with pink heart brooch,


### 3. 上色质感 (rendering & texture)
// NOTE: 也是和色彩差不多的结论. 
- `flat color` 平涂
- `thick painting, impasto` 厚涂
- `semi-thick painting` 半厚涂
- `watercolor` 水彩
- `ink wash` 水墨
- `sketch` 素描感
- `clean digital art` 干净数码
- `smooth, brushless rendering` 无笔触平滑
- `glossy, glistening skin` 油亮
- `wet, sweaty skin` 汗湿水润
- `jelly-like skin` 果冻肌
- `pearlescent skin` 珍珠质感
- `matte` 哑光
- `transparent, airy feel` 透明感/空气感
- `translucent fabric` 半透明衣物/薄纱
- `silk texture` 丝绸质感
- `metallic reflections` 金属反光/漆光
- `latex, patent leather` 漆皮/乳胶
- `detailed fabric folds` 细致褶皱
- `elaborate lace and accessories` 繁复蕾丝饰品
- `skin fuzz, peach fuzz` 绒毛
- `grainy, noisy texture` 颗粒噪点
- `retro print texture` 复古印刷质感
- `halftone` 网点

### 4. 线条 (lineart)
// 结论和上述差不多，总体对画面影响很有限
- `thick outlines` 粗描边
- `thin delicate lines` 细线
- `colored lineart` 有色线稿/彩线
- `de-emphasized lineart` 弱化线稿
- `rough sketchy lines` 草稿粗犷
- `clean precise lineart` 工整
- `broken lines` 断线/断笔
- `strong line weight variation` 线宽变化强
- `lineless, painterly` 无线稿
- `sharp angular lines` 锐利尖锐
- `round soft lines` 圆润

### 5. 人体形态 (figure)
// 这个tag不属于氛围，放到中间比较合适，不要放在开头或者结尾
// 这个开始影响大了
- `chibi` Q版头身
- `elongated proportions` 修长(模特比)
- `slender` 纤细
- `plump, curvy` 肉感
- `soft, squishy flesh` 软糯弹性
- `flesh compression, squeeze marks` 挤压勒痕
- `hourglass figure` 沙漏型
- `wide hips, thick thighs` 宽胯厚腿
- `gravity sag` 下垂感
- `baby face with mature body` 童颜肉身
- `muscular` 肌肉
- `detailed anatomy` 写实骨骼肌肉
- `realistic skin texture` 写实皮肤(毛孔/质感)
- `flat anime skin` 平面动画皮肤
- `detailed hands` 精致手部
- `simplified forms` 简化形体

### 6. 脸部 (face)
// 这个tag不属于氛围，放到中间偏开头比较合适（1girl, solo, 角色tag, 一两个general标签, _here_）
// 这个开始影响大了
- `round face` 圆脸
- `sharp face` 锐利尖脸
- `big anime eyes` 大眼动画比
- `narrow realistic eyes` 细长写实比
- `jewel-like eyes` 宝石瞳
- `multi-layered iris` 多层虹膜
- `sparkle eyes, star-shaped highlights` 碎星/星形高光
- `heart-shaped highlights` 心形高光
- `spiral eyes` 螺旋瞳
- `geometric iris highlights` 几何高光瞳
- `detailed irises and highlights` 精致虹膜高光
- `simple eyes` 简化点眼
- `heavy eyelashes` 浓密睫毛
- `under-eye makeup` 下眼影/泪袋
- `dazed, unfocused eyes` 涣散迷离
- `droopy eyes` 下垂眼
- `upturned narrow eyes` 上扬猫眼
- `wide-set eyes` 宽眼距
- `gradient blush` 渐变腮红
- `heavy blush` 浓腮红
- `parted lips` 微张唇
- `glossy full lips` 水润厚唇
- `fang` 小虎牙
- `painterly face` 厚涂立体脸
- `flat face` 平面脸
- `detailed hair strands` 细致发丝
- `airy hair` 空气感发丝
- `gradient, translucent hair tips` 渐变透明发梢

### 7. 气质年龄感 (character vibe)
// 结论和人体形态一致
- `childlike` 幼态
- `mature` 成熟
- `elegant, refined` 优雅精致
- `casual` 随意休闲
- `innocent` 清纯
- `sensual` 色气
- `innocent yet alluring` 纯欲
- `cute` 可爱
- `lively, energetic` 活泼
- `gentle` 温柔
- `cool, aloof` 高冷
- `mischievous` 俏皮
- `shy, embarrassed` 羞涩
- `tipsy, hazy` 微醺
- `melancholic` 忧郁
- `fragile, sickly look` 病弱易碎
- `yandere` 病娇
- `jaded, world-weary` 厌世

// TODO: remove this 因为不属于style

<!-- ### 8. 构图镜头 (composition)
- `close-up` 特写
- `portrait` 头像
- `bust shot` 半身
- `wide shot` 远景
- `tiny figure in vast landscape` 大景小人
- `from above` 俯视
- `from below` 仰视
- `fisheye lens` 鱼眼
- `wide-angle lens` 广角
- `extreme foreshortening` 夸张前后透视
- `dynamic perspective, dutch angle` 动态倾斜
- `diagonal composition` 对角线构图
- `off-balance pose` 非平衡姿态
- `static centered composition` 静止居中
- `candid, snapshot moment` 抓拍瞬间
- `pov, first-person view` 第一人称视角
- `voyeuristic framing` 窥视感
- `detailed background` 繁复背景
- `simple background, white background` 留白/纯色
- `cluttered composition, high detail density` 满溢高信息密度
- `floating particles, fragments` 悬浮粒子碎片 -->

### 9. 氛围情绪 (atmosphere)
// NOTE: 没啥作用 可能需要移除
- `healing, cozy` 治愈
- `lonely, melancholic` 孤独忧郁
- `dreamy, ethereal` 梦幻缥缈
- `sacred, divine atmosphere` 神圣感
- `epic, solemn atmosphere` 史诗感
- `gritty realism` 粗粝写实
- `slice-of-life calm` 日常感
- `dramatic` 戏剧化
- `nostalgic` 怀旧
- `futuristic, sterile` 科幻冷感
- `liminal space` 临界空间感

### 10. 时代/媒介戏仿 (era & medium pastiche)
// TODO: 这个感觉也没啥用
- `1980s retro anime style` 80年代复古动画
- `1990s anime style` 90年代复古动画
- `modern clean digital style` 现代清晰
- `cel animation look` 赛璐璐胶片感
- `black and white manga with screentone` 黑白漫画+网点纸
- `korean illustration style` 韩系
- `commercial illustration style` 商业插画感
- `fashion magazine style` 时尚杂志感
- `galgame illustration style` galgame审美
- `figurine-like rendering` 手办感
- `pop art style` 波普
- `glitch art` 故障风
- `impressionist style` 印象派
- `ukiyo-e style` 浮世绘
- `stained glass style` 彩绘玻璃
- `art nouveau` 新艺术
- `art deco, decorative style` 装饰主义
- `retro poster` 老海报
- `pencil sketch` 铅笔
- `charcoal drawing` 炭笔

