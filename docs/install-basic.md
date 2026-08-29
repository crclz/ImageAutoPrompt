## 工作流配置

1. 首先明确，entropy/conf/workflows/workflow.example.json 不可以直接使用，只能作为参考
2. 本工具支持任意工作流的原理，是用户在工作流中插入一些标志字符串，它们可被替换
3. 前往comfyui，我们需要将你的工作流做出如下改动：
   - 负面提示词：固定负面提示词为你模型需要的。为了探索过程稳定，我们不对负面提示词进行探索。
   - 正面提示词：将提示词拆分为2个输入，一个输入留前缀或后缀固定质量tag，另一个输入填写 `entropy:positive`，前后不能有空格 (用于字符串替换)，二者配置concat。
   - 图片输出：仅支持1个图片输出。请使用图片保存节点，将地址或者前缀改为 `entropy:output_image` (用于读取图片输出)
4. 点击comfyui的导出(API)，将下载的json放到 entropy/conf/workflows/ 目录


## 启动

启动server: 在仓库根目录，运行 `flask --app server run`，点击链接，进入网页
