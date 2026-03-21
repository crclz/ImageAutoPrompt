# ImageAutoPrompt

## 简介

ImageAutoPrompt适用于需探索prompt的AI图片内容创作场景，它尝试解决以下几个问题：
- 更快、更准确的prompt半自动探索
- 更高效的artist串探索和权重调整
- 显卡0空转，不间断探索更满意的图片

效果展示: ___

## 环境需求

技能需求：
- 会使用基础的linux或者windows命令
- 会使用简单的git命令和python相关命令
- 或者会利用大模型解决问题

环境：
- python 3.12 或者以上
- 安装和前置准备阶段，有GPU会更快，无GPU也行。正式使用阶段无需GPU。
- 能访问github，或者知道如何利用代理

安装过程

1. git clone 本仓库到某一路径

2. 安装 python。最好使用miniconda新建环境，没有也行，应该没啥冲突。

3. 导出python依赖
```bash
# 从pyproject.toml导出依赖到 requirements.txt
pip install toml
python export_requirements.py
```
如果你会安装cuda，那么请编辑 requirements.txt 文件。不会也没关系。


4. 安装依赖，使用清华pypi加速。
```bash
pip install -r requirements.txt -i http://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

现在你的环境就搭建好了，能使用最主要的功能了。

进阶RAG功能需要依赖10-40分钟的建库过程，也挺关键，需要GPU算embedding建库，后文再讲。


## ComfyUI配置

1. 将 app_config.example.yaml 复制到 app_config.yaml，这是程序的主要配置。
2. 进入 app_config.yaml 看看，我们需要编辑一些字段
   - comfyui_base_url: 这个是你comfyui的端口地址。
   - 本工具会通过这个地址调用comfyui，可调用自己的工作量，填入提示词，然后获取图片输出
   - workflow_api_json: 这个是comfyui工作流api json。你需要将自己的工作流进行轻微编辑后，导出(API)到对应的地址。
   - prompt_file: 这个是prompt，先不用看
   - invalid_tag_tolerance: 保持9999，因为目前还没有配置好RAG功能
   - 其他配置：不用看

3. workflow_api_json的处理
   - 首先明确，workflows/workflow.example.json 不可以直接使用，只能作为参考
   - 本工具支持任意工作量的原理，是用户在工作流中插入一些标志字符串，它们可被替换
   - 前往comfyui，我们需要将你的工作流做出如下改动：
     - 负面提示词：固定负面提示词为你模型需要的。为了探索过程稳定，我们不对负面提示词进行探索。
     - 正面提示词：将提示词拆分为2个输入，一个输入留前缀或后缀固定质量tag，另一个输入填写 `entropy:positive`，前后不能有空格 (用于字符串替换)
     - 图片输出：仅支持1个图片输出。请使用图片保存节点，将地址或者前缀改为 `entropy_out_placeholder` (用于读取图片输出)
   - 点击comfyui的导出(API)，将下载的json放到上文workflow_api_json配置文件中填写的位置


## 核心功能：prompt探索

### 运行初始prompt

1. 启动server: 在仓库根目录，运行 flask --app server run，点击链接，进入网页
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
9. 你会观测到 invalid tags 增多，并且可能会观测到图像不稳定。
    - 如果遇见这个问题，说明自然语言太多，标准tag少。后文会有RAG模块解决。


## 功能：tag纠错与灵感 (RAG)



# run server

flask --app server run

开发的时候，加--debug以享受hot reload


## datasets

10w: https://gist.githubusercontent.com/pythongosssss/1d3efa6050356a08cea975183088159a/raw/a18fb2f94f9156cf4476b0c24a09544d6c0baec6/danbooru-tags.txt

jupyter nbconvert --to script --output rag_build.tmp .\test_notebooks\rag_build.ipynb   