
## RAG建库

1. 安装 torch + gpu （CPU也完全没问题），如果你想建库快点的话。 https://pytorch.org/get-started/locally/

2. 将建库notebook文件导出为python文件
```bash
jupyter nbconvert --to script --output rag_build.tmp ./test_notebooks/rag_build.ipynb   
```

3. 运行建库python文件
```bash
python ./test_notebooks/rag_build.tmp.py
```

这会进行几个事情：
- 下载embedding模型(2G+)，到ai_models文件夹
- 进行建库，到 database 目录


4. 建库完成后，启动 `python server.py`（需先 `uv sync` 全量安装 rag 组依赖，见 install-environment skill）

5. 来到rag网页，输入“鸟语花香”，然后等（首次加载模型会慢，后面光速）
   - 结果中召回了很多相关的词，能提供灵感

6. 输入"using a bike"，你会发现有一定的纠错能力“riding bicycle”，以及灵感能力“pushing bicycle”

7. 自己编写提示词，也可以适当使用这个页面
