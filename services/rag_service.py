"""
描述: RAG 问答服务
主要功能:
    - 向量检索
    - 生成答案
    - 构造引用
依赖: psycopg
"""

from __future__ import annotations

from psycopg import Connection

from schemas.rag import QACitation, QAResponse
from services.model_service import chat
from services.vector_service import search_document_nodes


# ============================================
# region _fetch_document_meta
# ============================================
def _fetch_document_meta(conn: Connection, doc_id: int) -> tuple[str | None, str | None]:
    row = conn.execute(
        """
        SELECT title, file_name FROM documents WHERE doc_id = %s
        """,
        (doc_id,),
    ).fetchone()
    if not row:
        return None, None
    return row[0], row[1]
# endregion
# ============================================


# ============================================
# region build_answer
# ============================================
def build_answer(conn: Connection, question: str, top_k: int, doc_id: int | None) -> QAResponse:
    """
    构建问答响应

    参数:
        conn: 数据库连接
        question: 问题
        top_k: 召回数量
        doc_id: 文档ID
    返回:
        问答响应
    """

    hits = search_document_nodes(conn, question, top_k, doc_id)
    citations: list[QACitation] = []

    meta_cache: dict[int, tuple[str | None, str | None]] = {}
    context_parts: list[str] = []
    for hit in hits:
        hit_doc_id = int(hit[0])
        node_id = int(hit[1])
        title = hit[2]
        content = hit[3]
        path = hit[4]
        party_a_name = hit[5]
        score = float(hit[7])

        if hit_doc_id not in meta_cache:
            meta_cache[hit_doc_id] = _fetch_document_meta(conn, hit_doc_id)
        doc_title, file_name = meta_cache[hit_doc_id]

        citations.append(
            QACitation(
                source_id=str(hit_doc_id),
                chunk_id=node_id,
                score=score,
                source_title=doc_title or title,
                file_name=file_name,
                path=path,
                party_a_name=party_a_name,
            )
        )

        context_parts.append(
            "\n".join(
                [
                    f"[Source {hit_doc_id}:{node_id}]",
                    f"Title: {title}",
                    f"Path: {' > '.join(path)}",
                    f"Content: {content}",
                ]
            )
        )

    context_block = "\n\n".join(context_parts)
    prompt = (
        "You are a RAG assistant. Answer the question using ONLY the context. "
        "Cite sources in the answer using [doc_id:node_id].\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context_block}"
    )

    response = chat(
        [
            {"role": "system", "content": "Answer in Chinese."},
            {"role": "user", "content": prompt},
        ]
    )

    answer = response.content or ""
    return QAResponse(answer=answer, citations=citations)
# endregion
# ============================================
