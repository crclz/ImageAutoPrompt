warning:

这是老readme，部分信息已经过期，部分信息有用

## 简介

ImageAutoPrompt适用于需探索prompt的AI图片内容创作场景，它尝试解决以下几个问题：
- 更快、更准确的prompt半自动探索
- 更高效的artist串探索和权重调整
- 显卡0空转，不间断探索更满意的图片

效果展示: https://www.bilibili.com/video/BV1UAAPzmEd9/

使用教程: https://www.bilibili.com/video/BV1BCAAzhEKs/



## 核心功能：prompt探索

### 运行初始prompt

1. 启动server: 在仓库根目录，运行 `flask --app server run`，点击链接，进入网页
2. 新建episode: 在episodes页面创建一个新episode，英文命名.
3. 深度阅读 prompts/prompt_recommended.md 的 prompt格式、输出格式这两个章节。看看里面的提示词是否符合你使用的模型的要求。例如质量词，例如提示词格式。
   - 强烈建议仔细查看并进行编辑。可存在多个文件，并利用上文 prompt_file 进行切换。
4. 简略阅读 prompts/prompt_recommended.md 章节，未来你大概率需要进行编辑，以提升效果
5. 构造初始文生图prompt，格式与 [prompts/prompt_recommended.md](prompts/prompt_recommended.md) 的末尾统一

例如这个
```prompt0
positive
1girl, solo, keqing \(genshin impact\),  long hair, looking at viewer, hair ornament, gloves, dress, holding, jewelry, bare shoulders, sitting, twintails, purple eyes, braid, purple hair, flower, pantyhose, outdoors, earrings, frills, food, one eye closed, detached 
sleeves, sky, day, cloud, hair bun, blue sky, black pantyhose, bird, eating, holding food, food on face, cone hair bun, neck tassel

negative
null
```

6. 在episode页面 paste prompt
7. 等待timestep=0生成图片，然后点击图片，不选择高分，直接提交。


### 进行artist（画师串）探索

prompts/prompt_recommended.md中预置了一些画师。你可以将你审美的画师进行总结，替换进prompt_recommended.md。

1. 复制High Score Chosen右边那串文字（点击即可）
   - 首次的会是包含了 prompts/prompt_recommended.md + 初始prompt的完整文字。
2. 粘贴给网页版的Gemini，或者其他任何。
   - 粘贴后别忙着提交，告诉它“仅仅帮我探索artist，除非我说可以探索其他”
3. 等待Gemini输出完成，将整个复制粘贴到 episode 页面的Paste Prompt弹框
4. 等待comfyui跑完，然后选择你最满意的，提交。你如果觉得退步了，啥也可不选择。
5. 复制给Gemini
6. 重复本过程，直到画风收敛到你满意的情况。
7. 如果你觉得Gemini提前固定了一些画师，你可随时要求扩大范围。反之亦然。
8. 画风满意后，你可要求自由探索：
   - 自然环境、社会环境
   - 外貌、语言、动作、心理、神态
   - 整体外貌、容貌五官、衣着服饰、姿态神情
9. 你会观测到prompt逐渐向你满意的方向靠拢。
10. 也可能会观测到 invalid tags 增多，并且可能会观测到图像不稳定。
    - 如果遇见这个问题，说明自然语言太多，标准tag少。后文会有RAG模块解决。


### 双buffer打满显卡

如果想要打满显卡，图像正在生成的时候，是可以再次复制的。

gemini会给出新的探索。这样你的显卡永远有事情做。


# 附录

## 如何总结画师

- 阶段1：收集N个画师，以自己的审美。
- 阶段2：对于每一个画师，选择你喜欢的5-6张，给gemini
    ```
    1. 帮我详细分析、总结一下这位画师的画风，说明理由
    2. 最后，用200字总结画风，不要求自然语言流畅，要求简要、分点答题、信息密度高
    ```
  保存到一个文档里。
- 阶段3：压缩。将那个文档（包含很多画师）粘贴给gemini.
    ```
    将下列画师信息进行压缩，不谈属性只谈值（例如“人物偏可爱”=>“可爱”），并保留最核心、最具特色的信息，让人直觉上能快速意会。

    输出```txt```格式。##标题不变，但每名画师尽量压缩在100字以内。不要求自然语言流畅，要求简要、信息密度高。
    ```
- 将压缩后的粘贴到 prompt里面

