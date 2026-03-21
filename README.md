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




## 功能：tag纠错与灵感 (RAG)


# install dependencies

TODO: no version restriction

# run server

flask --app server run

开发的时候，加--debug以享受hot reload


## datasets

10w: https://gist.githubusercontent.com/pythongosssss/1d3efa6050356a08cea975183088159a/raw/a18fb2f94f9156cf4476b0c24a09544d6c0baec6/danbooru-tags.txt

jupyter nbconvert --to script --output rag_build.tmp .\test_notebooks\rag_build.ipynb   