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
    ChatHistoryResponse,
    ChatMessageItem,
    ChatMessageRequest,
    ChatSessionCreateRequest,
    ChatSessionCreateResponse,
)
from services.chat_service import (
    append_message,
    create_session,
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

    messages = [
        ChatMessageItem(
            message_id=int(item["message_id"]),
            role=str(item["role"]),
            content=str(item["content"]),
            citations=item.get("citations", []),
            created_at=str(item.get("created_at")),
        )
        for item in history
    ]

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
            _, citations, context_block = retrieve_with_context(
                conn, payload.content, truncated, payload.top_k, payload.doc_id
            )

            yield _sse_event("status", {"state": "GENERATE", "step": 2, "total": 3})
            answer = generate_answer(payload.content, context_block, history_text)

            chunk_size = 200
            for i in range(0, len(answer), chunk_size):
                yield _sse_event("chunk", {"content": answer[i : i + chunk_size]})

            citations_payload = [
                {
                    "source_id": c.source_id,
                    "node_id": c.chunk_id,
                    "score": c.score,
                    "path": c.path,
                }
                for c in citations
            ]
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
