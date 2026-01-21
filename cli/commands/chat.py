"""
描述: 终端对话 CLI
主要功能:
    - SSE 交互式对话
依赖: typer
"""

from __future__ import annotations

import json
import os
import sys
from typing import Iterable
from urllib.request import Request, urlopen

import typer

app = typer.Typer(help="Chat session commands")


# ============================================
# region _get_base_url
# ============================================
def _get_base_url(api_base: str | None) -> str:
    if api_base:
        return api_base.rstrip("/")
    host = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port = os.getenv("FASTAPI_PORT", "8000")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    return f"http://{host}:{port}"
# endregion
# ============================================


# ============================================
# region _post_json
# ============================================
def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}
# endregion
# ============================================


# ============================================
# region _get_json
# ============================================
def _get_json(url: str) -> dict[str, object]:
    request = Request(url, method="GET")
    with urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}
# endregion
# ============================================


# ============================================
# region _iter_sse
# ============================================
def _iter_sse(response) -> Iterable[tuple[str, str]]:
    event = "message"
    data_lines: list[str] = []

    while True:
        line = response.readline()
        if not line:
            break
        decoded = line.decode("utf-8").rstrip("\n")

        if decoded.startswith("event:"):
            event = decoded[len("event:") :].strip()
            continue
        if decoded.startswith("data:"):
            data_lines.append(decoded[len("data:") :].strip())
            continue
        if decoded.strip() == "":
            data = "\n".join(data_lines).strip()
            yield event, data
            event = "message"
            data_lines = []

    if data_lines:
        data = "\n".join(data_lines).strip()
        yield event, data
# endregion
# ============================================


# ============================================
# region _send_sse_message
# ============================================
def _send_sse_message(
    base_url: str,
    session_id: str,
    content: str,
    top_k: int,
    doc_id: int | None,
) -> None:
    url = f"{base_url}/chat/sessions/{session_id}/messages"
    payload = {"content": content, "top_k": top_k, "doc_id": doc_id}
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})

    with urlopen(request, timeout=300) as response:
        for event, data in _iter_sse(response):
            if event == "status":
                payload = json.loads(data)
                typer.echo(f"[{payload.get('state')}] {payload.get('step')}/{payload.get('total')}")
            elif event == "chunk":
                payload = json.loads(data)
                typer.echo(payload.get("content", ""), nl=False)
                typer.echo("", nl=False)
            elif event == "message":
                payload = json.loads(data)
                typer.echo("\n")
                typer.echo(payload.get("content", ""))
                citations = payload.get("citations", [])
                if citations:
                    typer.echo("Citations:")
                    for cite in citations:
                        typer.echo(
                            f"- {cite.get('source_id')}:{cite.get('node_id')} score={cite.get('score')}"
                        )
            elif event == "error":
                payload = json.loads(data)
                typer.echo(f"Error: {payload.get('code')}: {payload.get('message')}")
            elif event == "done":
                payload = json.loads(data)
                typer.echo(f"Done: message_id={payload.get('message_id')}")
# endregion
# ============================================


# ============================================
# region _print_history
# ============================================
def _print_history(base_url: str, session_id: str) -> None:
    url = f"{base_url}/chat/sessions/{session_id}/history"
    data = _get_json(url)
    raw_messages = data.get("messages", [])
    messages = raw_messages if isinstance(raw_messages, list) else []
    for msg in messages:
        if isinstance(msg, dict):
            typer.echo(f"{msg.get('role')}: {msg.get('content')}")
# endregion
# ============================================


# ============================================
# region chat
# ============================================
@app.command("chat")
def chat(
    api_base: str | None = typer.Option(None, help="API Base URL"),
    session_id: str | None = typer.Option(None, help="会话ID"),
    user_id: str | None = typer.Option(None, help="用户ID"),
    doc_id: int | None = typer.Option(None, help="文档ID"),
    top_k: int = typer.Option(5, help="召回数量"),
) -> None:
    """
    SSE 交互式对话
    """

    base_url = _get_base_url(api_base)

    if not session_id:
        payload = _post_json(f"{base_url}/chat/sessions", {"user_id": user_id})
        session_id = str(payload.get("session_id"))
        typer.echo(f"Session: {session_id}")

    typer.echo("Enter message (/exit /new /history)")
    while True:
        try:
            content = typer.prompt(">")
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nBye")
            break

        if content.strip() == "":
            continue
        if content == "/exit":
            typer.echo("Bye")
            break
        if content == "/new":
            payload = _post_json(f"{base_url}/chat/sessions", {"user_id": user_id})
            session_id = str(payload.get("session_id"))
            typer.echo(f"Session: {session_id}")
            continue
        if content == "/history":
            _print_history(base_url, session_id)
            continue

        _send_sse_message(base_url, session_id, content, top_k, doc_id)
# endregion
# ============================================
