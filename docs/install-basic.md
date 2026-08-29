## ComfyUI配置

1. 将 entropy/conf/app_config.example.yaml 复制为 entropy/conf/app_config.yaml，这是程序的主要配置。
2. 进入 entropy/conf/app_config.yaml 看看，我们需要编辑一些字段
   - comfyui_base_url: 这个是你comfyui的端口地址。
   - 本工具会通过这个地址调用comfyui，可调用自己的工作流，填入提示词，然后获取图片输出
   - workflow_api_json: 这个是comfyui工作流api json。你需要将自己的工作流进行轻微编辑后，导出(API)到对应的地址。
   - invalid_tag_tolerance: 保持9999，因为目前还没有配置好RAG功能
   - 其他配置：不用看

3. workflow_api_json的处理
   - 首先明确，entropy/conf/workflows/workflow.example.json 不可以直接使用，只能作为参考
   - 本工具支持任意工作流的原理，是用户在工作流中插入一些标志字符串，它们可被替换
   - 前往comfyui，我们需要将你的工作流做出如下改动：
     - 负面提示词：固定负面提示词为你模型需要的。为了探索过程稳定，我们不对负面提示词进行探索。
     - 正面提示词：将提示词拆分为2个输入，一个输入留前缀或后缀固定质量tag，另一个输入填写 `entropy:positive`，前后不能有空格 (用于字符串替换)，二者配置concat。
     - 图片输出：仅支持1个图片输出。请使用图片保存节点，将地址或者前缀改为 `entropy:output_image` (用于读取图片输出)
   - 点击comfyui的导出(API)，将下载的json放到上文workflow_api_json配置文件中填写的位置


## 启动

启动server: 在仓库根目录，运行 `flask --app server run`，点击链接，进入网页
