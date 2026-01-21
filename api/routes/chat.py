"""
描述: 对话会话路由
主要功能:
    - 会话创建
    - SSE 对话消息
    - 会话历史查询
依赖: fastapi
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from db.connection import get_connection, get_database_url
from schemas.chat import (
    ChatCitation,
    ChatHistoryResponse,
    ChatMessageItem,
    ChatMessageRequest,
    ChatSessionItem,
    ChatSessionCreateRequest,
    ChatSessionCreateResponse,
)
from services.chat_service import (
    append_message,
    create_session,
    get_recent_sessions,
    get_recent_history,
    truncate_history_by_chars,
)
from services.rag_service import generate_answer, retrieve_with_context

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================
# region _sse_event
# ============================================
def _sse_event(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
# endregion
# ============================================


# ============================================
# region _build_preview
# ============================================
def _build_preview(text: str, limit: int = 50) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."
# endregion
# ============================================


# ============================================
# region list_chat_sessions
# ============================================
@router.get("/sessions", response_model=list[ChatSessionItem])
def list_chat_sessions(limit: int = 10) -> list[ChatSessionItem]:
    """
    列出最近会话
    """

    db_url = get_database_url()
    with get_connection(db_url) as conn:
        sessions = get_recent_sessions(conn, limit)

    items: list[ChatSessionItem] = []
    for session in sessions:
        raw_session_id = session.get("session_id")
        session_id = str(raw_session_id) if raw_session_id is not None else ""
        title = session.get("title")
        message_count = session.get("message_count")
        updated_at = session.get("updated_at")
        message_count_value = message_count if isinstance(message_count, int) else 0
        items.append(
            ChatSessionItem(
                session_id=session_id,
                title=str(title) if isinstance(title, str) else None,
                message_count=message_count_value,
                updated_at=str(updated_at) if updated_at is not None else None,
            )
        )
    return items
# endregion
# ============================================


# ============================================
# region create_chat_session
# ============================================
@router.post("/sessions", response_model=ChatSessionCreateResponse)
def create_chat_session(payload: ChatSessionCreateRequest) -> ChatSessionCreateResponse:
    """
    创建会话
    """

    db_url = get_database_url()
    with get_connection(db_url) as conn:
        session_id, title = create_session(conn, payload.user_id)
    return ChatSessionCreateResponse(session_id=session_id, title=title)
# endregion
# ============================================


# ============================================
# region get_chat_history
# ============================================
@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
def get_chat_history(session_id: str) -> ChatHistoryResponse:
    """
    获取会话历史
    """

    db_url = get_database_url()
    with get_connection(db_url) as conn:
        history = get_recent_history(conn, session_id, limit=20)

    messages: list[ChatMessageItem] = []
    for item in history:
        citations = item.get("citations", [])
        raw_message_id = item.get("message_id")
        if isinstance(raw_message_id, int):
            message_id = raw_message_id
        elif isinstance(raw_message_id, str) and raw_message_id.isdigit():
            message_id = int(raw_message_id)
        else:
            message_id = 0
        citation_items: list[ChatCitation] = []
        if isinstance(citations, list):
            for cite in citations:
                if isinstance(cite, dict):
                    citation_items.append(ChatCitation(**cite))
        messages.append(
            ChatMessageItem(
                message_id=message_id,
                role=str(item.get("role") or ""),
                content=str(item.get("content") or ""),
                citations=citation_items,
                created_at=str(item.get("created_at")),
            )
        )

    return ChatHistoryResponse(session_id=session_id, messages=messages)
# endregion
# ============================================


# ============================================
# region send_chat_message
# ============================================
@router.post("/sessions/{session_id}/messages")
async def send_chat_message(session_id: str, request: Request) -> StreamingResponse:
    """
    SSE 发送消息
    """

    payload_json = await request.json()
    payload = ChatMessageRequest(**payload_json)

    async def event_stream() -> AsyncGenerator[str, None]:
        db_url = get_database_url()
        with get_connection(db_url) as conn:
            history = get_recent_history(conn, session_id, limit=20)
            truncated = truncate_history_by_chars(history, max_chars=2000)

            append_message(conn, session_id, "user", payload.content)

            history_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in truncated]
            )
            history_text = history_text.strip()

            yield _sse_event("status", {"state": "RETRIEVE", "step": 1, "total": 3})
            hits, citations, context_block = retrieve_with_context(
                conn, payload.content, truncated, payload.top_k, payload.doc_id
            )

            yield _sse_event("status", {"state": "GENERATE", "step": 2, "total": 3})
            answer = generate_answer(payload.content, context_block, history_text)

            chunk_size = 200
            for i in range(0, len(answer), chunk_size):
                yield _sse_event("chunk", {"content": answer[i : i + chunk_size]})

            preview_map: dict[tuple[int, int], str] = {}
            for hit in hits:
                hit_doc_id = int(hit[0])
                node_id = int(hit[1])
                content = str(hit[3] or "")
                preview_map[(hit_doc_id, node_id)] = _build_preview(content)

            citations_payload = []
            for cite in citations:
                key = (int(cite.source_id), int(cite.chunk_id))
                filename = cite.file_name or cite.source_title
                citations_payload.append(
                    {
                        "document_id": cite.source_id,
                        "filename": filename,
                        "chunk_index": cite.chunk_id,
                        "preview": preview_map.get(key),
                        "score": cite.score,
                        "source_id": cite.source_id,
                        "node_id": cite.chunk_id,
                        "path": cite.path,
                    }
                )
            message_id = append_message(
                conn,
                session_id,
                "assistant",
                answer,
                citations_payload,
            )

            yield _sse_event(
                "message",
                {
                    "role": "assistant",
                    "content": answer,
                    "citations": citations_payload,
                },
            )
            yield _sse_event("done", {"message_id": message_id})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
# endregion
# ============================================
