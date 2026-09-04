import argparse

import toml


def main():
    parser = argparse.ArgumentParser(description="从 pyproject.toml 导出 requirements.txt")
    parser.add_argument(
        "--rag",
        action="store_true",
        help="追加 rag 依赖组（chromadb/modelscope/sentence-transformers/torch）",
    )
    args = parser.parse_args()

    # 读取并解析
    data = toml.load("pyproject.toml")

    requirements = list(data["project"]["dependencies"])
    if args.rag:
        requirements += data["dependency-groups"]["rag"]

    # 提取并保存
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))


if __name__ == "__main__":
    main()
