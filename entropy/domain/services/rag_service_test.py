import pytest

from entropy.domain.services.rag_service import RagService


@pytest.mark.slow  # 加载 bge-m3 模型 + chromadb
def test_rag_simple_happy_1():
    query = "女性华丽服饰"

    tags, scores = RagService.rag_simple(query, 10)

    for tag, score in zip(tags, scores):
        print(f"{tag} {score}")
