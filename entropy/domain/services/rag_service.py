import logging
import os
import threading
import time

_logger = logging.getLogger(__name__)

# Thread-safe lazy singletons
_lock = threading.Lock()
_danbooru_tags_collection = None
_embedding_model = None
_reranker_model = None


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


def reranker_model():
    global _reranker_model
    if _reranker_model is None:
        with _lock:
            if _reranker_model is None:  # double-checked locking
                raise ValueError("Not supported")
                import torch
                from FlagEmbedding import FlagReranker

                device = "cuda" if torch.cuda.is_available() else "cpu"

                _reranker_model = FlagReranker(
                    r"C:\Users\ThePlayer\.cache\huggingface\hub\models--BAAI--bge-reranker-v2-m3\snapshots\953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
                    device=device,
                    use_fp16=True,
                    local_files_only=True,
                )
    return _reranker_model


class RagService:
    @classmethod
    def do_rag(cls, query_text: str, recall_count: int = 500, rerank_output: int = 20) -> tuple[list[str], list[float]]:
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

    @classmethod
    def batch_rag(
        cls, query_text_list: list[str], recall_count: int = 500, rerank_output: int = 20
    ) -> list[tuple[list[str], list[float]]]:
        if not query_text_list:
            return []

        # 1. 批量生成 Embedding
        # 假设 embedding_model().encode 支持传入 List[str]
        query_embeddings = embedding_model().encode(query_text_list, normalize_embeddings=True).tolist()

        # 2. 向量空间批量检索 (ChromaDB/Milvus 等通常支持 query 传入 list)
        results = danbooru_tags_collection().query(
            query_embeddings=query_embeddings,
            n_results=recall_count,
        )

        # 提取候选文档，results["documents"] 的结构通常是 List[List[str]]
        all_candidates_list = results["documents"]

        assert isinstance(all_candidates_list, list)

        for candidates in all_candidates_list:
            for i in range(len(candidates)):
                candidates[i] = candidates[i].replace("_", " ")

        if rerank_output == 0:
            return [(p, []) for p in all_candidates_list]

        # 3. 准备重排序的输入对
        # Reranker 通常在处理这种结构化数据时，一次性传入所有 pairs 最快
        all_pairs = []
        for i, query in enumerate(query_text_list):
            candidates = [p.replace("_", " ") for p in all_candidates_list[i]]
            for cand in candidates:
                all_pairs.append([query, cand])

        # 4. 批量计算重排序得分
        # 注意：如果 all_pairs 非常大（如 100个 query * 500 recall = 5万对），
        # 建议在外部或模型层级处理 batch_size，防止显存溢出
        all_scores = reranker_model().compute_score(all_pairs)

        # 5. 后处理：将平铺的得分重新对应到每个 query 并排序
        final_results = []
        score_idx = 0
        for i, query in enumerate(query_text_list):
            # 获取当前 query 对应的候选集数量
            current_candidates = [p.replace("_", " ") for p in all_candidates_list[i]]  # type: ignore
            num_cands = len(current_candidates)

            # 截取对应的得分段
            current_scores = all_scores[score_idx : score_idx + num_cands]
            score_idx += num_cands

            # 排序并截取 top N
            reranked = sorted(zip(current_candidates, current_scores), key=lambda x: x[1], reverse=True)

            top_tags = [str(t) for t, s in reranked[:rerank_output]]
            top_scores = [float(s) for t, s in reranked[:rerank_output]]

            final_results.append((top_tags, top_scores))

        return final_results

    @classmethod
    def batch_rag_simple(cls, query_text_list: list[str], recall_count: int) -> list[tuple[list[str], list[float]]]:
        if not query_text_list:
            return []

        # 1. 批量生成 Embedding
        # 假设 embedding_model().encode 支持传入 List[str]
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
