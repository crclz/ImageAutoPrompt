from entropy.domain.services.rag_service import RagService


def test_do_rag_happy_1():
    query = "女性华丽服饰"

    tags, scores = RagService.do_rag(query)

    for tag, score in zip(tags, scores):
        print(f"{tag} {score}")