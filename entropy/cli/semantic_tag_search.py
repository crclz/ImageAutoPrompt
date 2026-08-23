"""
对 danbooru tag 做语义搜索（调用本服务的 /api/show-rag）。

用法:
    uv run entropy/cli/semantic_tag_search.py --query "red hair"
    uv run entropy/cli/semantic_tag_search.py --query "red hair" "blue eyes"
"""

import argparse
import sys

# 约定在仓库根运行：将当前目录加入 sys.path（entropy 是 namespace package，未安装到环境中）
sys.path.append(".")

from entropy.infra.rag_proxy import RagProxy, ShowRagRequest


def main():
    # 1. 创建解析器对象
    parser = argparse.ArgumentParser()

    # 2. 添加必要的参数
    # metavar 给参数起个好听的名字，help 是说明文字
    parser.add_argument("--query", metavar="query", nargs="+", type=str, help="the query, english or chinese")

    # 3. 解析命令行输入
    args = parser.parse_args()

    queries = args.query

    if not queries:
        raise ValueError("query is empty")

    for q in queries:
        print(f"searching {q}. result: tag, distance (lower is better)")
        response = RagProxy.Rag(ShowRagRequest(query_text=q))

        for candidate in response.candidates:
            print(f"{candidate.text} {candidate.score:.2f}")

        print("\n")


if __name__ == "__main__":
    main()
