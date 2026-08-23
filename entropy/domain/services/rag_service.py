import logging
import os
import threading
import time

_logger = logging.getLogger(__name__)

# Thread-safe lazy singletons
_lock = threading.Lock()
_danbooru_tags_collection = None
_embedding_model = None


def danbooru_tags_collection():
    global _danbooru_tags_collection
    if _danbooru_tags_collection is None:
        with _lock:
            if _danbooru_tags_collection is None:  # double-checked locking
                t0 = time.perf_counter()
                _logger.info("loading danbooru_tags collection from chroma...")

                os.environ["ANONYMOUS_TELEMETRY"] = "False"
                import chromadb

                _logger.info("lazy import chromadb done in %.2fs", time.perf_counter() - t0)

                t0 = time.perf_counter()
                client = chromadb.PersistentClient(path="./database/chroma_1")
                _danbooru_tags_collection = client.get_collection(name="danbooru_tags")
                _logger.info("danbooru_tags collection loaded in %.2fs", time.perf_counter() - t0)
    return _danbooru_tags_collection


def embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with _lock:
            if _embedding_model is None:  # double-checked locking
                t0 = time.perf_counter()
                _logger.info("lazy import sentence_transformers...")

                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                from sentence_transformers import SentenceTransformer

                _logger.info("lazy import sentence_transformers done in %.2fs", time.perf_counter() - t0)

                t0 = time.perf_counter()
                _logger.info("loading embedding model bge-m3...")

                # TODO: replace with relative path inside repository
                _embedding_model = SentenceTransformer(
                    r"./ai_models/BAAI/bge-m3",
                    device="cpu",
                    local_files_only=True,
                )
                _logger.info("embedding model loaded in %.2fs", time.perf_counter() - t0)
    return _embedding_model


class RagService:
    @classmethod
    def batch_rag_simple(cls, query_text_list: list[str], recall_count: int) -> list[tuple[list[str], list[float]]]:
        if not query_text_list:
            return []

        # 1. 批量生成 Embedding
        query_embeddings = embedding_model().encode(query_text_list, normalize_embeddings=True).tolist()

        # 2. 向量空间批量检索 (ChromaDB/Milvus 等通常支持 query 传入 list)
        results = danbooru_tags_collection().query(
            query_embeddings=query_embeddings,
            n_results=recall_count,
        )

        distances = results["distances"]
        assert isinstance(distances, list)

        # 提取候选文档，results["documents"] 的结构通常是 List[List[str]]
        all_candidates_list = results["documents"]
        assert all_candidates_list

        for candidates in all_candidates_list:
            for i in range(len(candidates)):
                candidates[i] = candidates[i].replace("_", " ")

        return list(zip(all_candidates_list, distances))

    @classmethod
    def rag_simple(cls, query_text: str, recall_count: int) -> tuple[list[str], list[float]]:
        r = cls.batch_rag_simple([query_text], recall_count)

        return r[0]
