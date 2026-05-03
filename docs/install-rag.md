
## RAG建库

1. 对应app_config.yaml配置: invalid_tag_tolerance建议填写3，但前提是你完成RAG建库（10-40分钟）。

2. 安装 torch + gpu （CPU也完全没问题），如果你想建库快点的话。 https://pytorch.org/get-started/locally/

3. 将建库notebook文件导出为python文件
```bash
jupyter nbconvert --to script --output rag_build.tmp ./test_notebooks/rag_build.ipynb   
```

4. 运行建库python文件
```bash
python ./test_notebooks/rag_build.tmp.py
```

这会进行几个事情：
- 下载embedding模型(2G+)，到ai_models文件夹
- 进行建库，到 database 目录


5. 建库完成后，启动 `flask --app server run`

6. 来到rag网页，输入“鸟语花香”，然后等（首次加载模型会慢，后面光速）
   - 结果中召回了很多相关的词，能提供灵感

7. 输入"using a bike"，你会发现有一定的纠错能力“riding bicycle”，以及灵感能力“pushing bicycle”

8. 自己编写提示词，也可以适当使用这个页面


## 标签纠错与灵感

修改 app_config.yaml配置: invalid_tag_tolerance

invalid_tag_tolerance：这个参数的含义是“容忍多少个无效tag”。基于标准的tag的组合是有意义的，但过多会影响稳定性。

粘贴时，如果无效tag超过阈值，那么就会被拦截。你需要复制这些信息给gemini，让它修改。

这会提升整个探索过程的稳定性。但如果稳定性没明显问题，那么不建议使用。

建议：
- 不同模型的这个值不能复用，必须具体尝试
- 同一模型，不同场景的这个值，也需要具体尝试
- 建议最开始先完全放开（填写9999），如果你的某一场景发现tag向自然语言漂移得太厉害了，严重影响了稳定性，就从一个值开始尝试，例如5.

extra_valid_tag_file: 额外的有效标签文本文件地址，会热加载。文本文件，一行一个tag。用于预置的tag缺失的情况。

