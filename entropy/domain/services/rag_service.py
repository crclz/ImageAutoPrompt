import functools
import logging
from typing import List, Tuple
import chromadb


@functools.cache
def danbooru_tags_collection():
    client = chromadb.PersistentClient(path="./database/chroma_1")
    collection = client.get_collection(name="danbooru_tags")

    return collection


@functools.cache
def embedding_model():
    from sentence_transformers import SentenceTransformer

    # TODO: replace with relative path inside repository
    embedding_model = SentenceTransformer(
        r"C:\Users\ThePlayer\.cache\huggingface\hub\models--BAAI--bge-m3\snapshots\5617a9f61b028005a4858fdac845db406aefb181",
        device="cpu",
        local_files_only=True,
    )

    return embedding_model


@functools.cache
def reranker_model():
    from FlagEmbedding import FlagReranker
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"

    logging.info(f"reranker model device: {device}")

    reranker = FlagReranker(
        r"C:\Users\ThePlayer\.cache\huggingface\hub\models--BAAI--bge-reranker-v2-m3\snapshots\953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
        device=device,
        use_fp16=True,
        local_files_only=True,
    )

    return reranker


class RagService:
    @classmethod
    def warmup(cls) -> None:
        """
        TODO: call when application start
        """

    @classmethod
    def do_rag(cls, query_text: str, recall_count: int = 500, rerank_output: int = 20) -> Tuple[List[str], List[float]]:
        """
        return: tags, scores
        """

        query_embedding = embedding_model().encode(query_text, normalize_embeddings=True).tolist()

        results = danbooru_tags_collection().query(
            query_embeddings=[query_embedding],
            n_results=recall_count,
        )

        candidates = results["documents"][0]  # type: ignore

        candidates = [p.replace("_", " ") for p in candidates]

        pairs = [[query_text, candidate] for candidate in candidates]

        # 计算得分 (分数越高越相关)
        scores = reranker_model().compute_score(pairs)  # type: ignore

        # 将得分与候选标签组合并排序
        reranked_results = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)  # type: ignore

        reranked_results = list(reranked_results)

        # 输出前 20 个最精准的结果
        tags = []
        scores = []
        for tag, score in reranked_results[:rerank_output]:  # type: ignore
            assert isinstance(tag, str)
            assert isinstance(score, float)

            tags.append(tag)
            scores.append(score)

        return tags, scores
