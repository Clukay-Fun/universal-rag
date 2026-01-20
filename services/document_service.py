"""
描述: 文档解析服务
主要功能:
    - MarkItDown 转 Markdown
    - Markdown 结构化为节点树
    - 可选持久化节点
依赖: markitdown, psycopg
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from markitdown import MarkItDown
from psycopg import Connection

from config.settings import get_settings
from schemas.document import DocumentNode, DocumentParseResponse, DocumentParseStats
from services.model_service import structure_document

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")


# ============================================
# region convert_to_markdown
# ============================================
def convert_to_markdown(file_path: str) -> tuple[str, str | None]:
    """
    转换文件为 Markdown

    参数:
        file_path: 文件路径
    返回:
        Markdown 内容与标题
    """

    converter = MarkItDown()
    result = converter.convert(file_path)
    return result.markdown, result.title
# endregion
# ============================================


# ============================================
# region persist_structure
# ============================================
def persist_structure(
    conn: Connection,
    doc_id: int,
    model_name: str,
    payload: dict[str, object] | None,
    raw_text: str | None,
    error: str | None,
) -> None:
    """
    持久化结构化结果

    参数:
        conn: 数据库连接
        doc_id: 文档ID
        model_name: 模型名称
        payload: 结构化 JSON
        raw_text: 原始文本
        error: 错误信息
    返回:
        None
    """

    payload_json = json.dumps(payload, ensure_ascii=False) if payload is not None else None
    conn.execute(
        """
        INSERT INTO document_structures (
            doc_id,
            model_name,
            payload,
            raw_text,
            error,
            created_at
        )
        VALUES (%s, %s, %s::jsonb, %s, %s, %s)
        """,
        (
            doc_id,
            model_name,
            payload_json,
            raw_text,
            error,
            datetime.utcnow(),
        ),
    )
    conn.commit()
# endregion
# ============================================


# ============================================
# region _extract_json_text
# ============================================
def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        lines = stripped.splitlines()
        if lines and lines[0].lower().startswith("json"):
            stripped = "\n".join(lines[1:])
    return stripped.strip()
# endregion
# ============================================


# ============================================
# region _build_nodes_from_structure
# ============================================
def _build_nodes_from_structure(payload: dict[str, object]) -> list[DocumentNode] | None:
    nodes_value = payload.get("nodes")
    if not isinstance(nodes_value, list) or not nodes_value:
        return None

    nodes: list[DocumentNode] = []
    for index, item in enumerate(nodes_value, start=1):
        if not isinstance(item, dict):
            continue
        node_id_value = item.get("node_id")
        try:
            node_id = int(node_id_value) if node_id_value is not None else index
        except (TypeError, ValueError):
            node_id = index

        parent_id = item.get("parent_id")
        if parent_id in ("", "null"):
            parent_id = None
        if parent_id is not None:
            try:
                parent_id = int(parent_id)
            except (TypeError, ValueError):
                parent_id = None

        level_value = item.get("level")
        try:
            level = int(level_value) if level_value is not None else 1
        except (TypeError, ValueError):
            level = 1

        title = item.get("title")
        title = str(title) if title is not None else "Section"
        content = item.get("content")
        content = str(content) if content is not None else ""

        nodes.append(
            DocumentNode(
                node_id=node_id,
                parent_id=parent_id,
                level=level,
                title=title,
                content=content,
            )
        )

    return nodes or None
# endregion
# ============================================


# ============================================
# region parse_markdown_nodes
# ============================================
def parse_markdown_nodes(markdown: str) -> list[DocumentNode]:
    """
    解析 Markdown 为节点结构

    参数:
        markdown: Markdown 内容
    返回:
        节点列表
    """

    nodes: list[DocumentNode] = []
    stack: list[tuple[int, int]] = []
    node_id = 0
    current_node: DocumentNode | None = None
    content_lines: list[str] = []

    # ============================================
    # region flush_content
    # ============================================
    def flush_content() -> None:
        nonlocal content_lines
        if current_node is None:
            return
        current_node.content = "\n".join(content_lines).strip()
        content_lines = []
    # endregion
    # ============================================

    for line in markdown.splitlines():
        match = HEADING_PATTERN.match(line.strip())
        if match:
            flush_content()
            level = len(match.group(1))
            title = match.group(2).strip()

            while stack and stack[-1][0] >= level:
                stack.pop()

            parent_id = stack[-1][1] if stack else None
            node_id += 1
            current_node = DocumentNode(
                node_id=node_id,
                parent_id=parent_id,
                level=level,
                title=title,
                content="",
            )
            nodes.append(current_node)
            stack.append((level, node_id))
            continue

        if current_node is None:
            node_id += 1
            current_node = DocumentNode(
                node_id=node_id,
                parent_id=None,
                level=1,
                title="Document",
                content="",
            )
            nodes.append(current_node)
            stack = [(1, node_id)]

        content_lines.append(line)

    flush_content()
    return nodes
# endregion
# ============================================


# ============================================
# region persist_document
# ============================================
def persist_document(
    conn: Connection,
    title: str | None,
    file_name: str | None,
    nodes: list[DocumentNode],
) -> int:
    """
    持久化文档节点

    参数:
        conn: 数据库连接
        title: 文档标题
        file_name: 文件名
        nodes: 节点列表
    返回:
        文档ID
    """

    now = datetime.utcnow()
    row = conn.execute(
        """
        INSERT INTO documents (title, file_name, created_at)
        VALUES (%s, %s, %s)
        RETURNING doc_id
        """,
        (title, file_name, now),
    ).fetchone()

    if not row:
        raise RuntimeError("Failed to persist document")

    doc_id = row[0]
    payloads = []
    for order_index, node in enumerate(nodes):
        payloads.append(
            {
                "doc_id": doc_id,
                "parent_id": node.parent_id,
                "level": node.level,
                "title": node.title,
                "content": node.content,
                "order_index": order_index,
                "created_at": now,
            }
        )

    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO document_nodes (
                doc_id,
                parent_id,
                level,
                title,
                content,
                order_index,
                created_at
            )
            VALUES (
                %(doc_id)s,
                %(parent_id)s,
                %(level)s,
                %(title)s,
                %(content)s,
                %(order_index)s,
                %(created_at)s
            )
            """,
            payloads,
        )

    conn.commit()
    return doc_id
# endregion
# ============================================


# ============================================
# region parse_document
# ============================================
def parse_document(
    file_path: str,
    file_name: str | None,
    include_markdown: bool,
    persist: bool,
    use_model_structure: bool = True,
    conn: Connection | None = None,
) -> DocumentParseResponse:
    """
    解析文档并结构化

    参数:
        file_path: 文件路径
        file_name: 文件名
        include_markdown: 是否返回 Markdown
        persist: 是否持久化
        use_model_structure: 是否调用模型结构化
        conn: 数据库连接
    返回:
        文档解析响应
    """

    markdown, title = convert_to_markdown(file_path)
    nodes = parse_markdown_nodes(markdown)
    doc_id = None
    structure_result = None
    structure_error = None
    structure_payload: dict[str, object] | None = None

    if use_model_structure:
        try:
            node_payload = [
                {
                    "node_id": node.node_id,
                    "parent_id": node.parent_id,
                    "level": node.level,
                    "title": node.title,
                    "content": node.content,
                }
                for node in nodes
            ]
            response = structure_document(markdown, node_payload)
            structure_result = response.content
            if structure_result:
                json_text = _extract_json_text(structure_result)
                payload = json.loads(json_text)
                structure_payload = payload if isinstance(payload, dict) else None
                structured_nodes = _build_nodes_from_structure(payload)
                if structured_nodes:
                    nodes = structured_nodes
        except Exception as exc:
            structure_error = str(exc)

    if persist:
        if conn is None:
            raise RuntimeError("Database connection is required for persistence")
        doc_id = persist_document(conn, title or Path(file_path).stem, file_name, nodes)
        persist_structure(
            conn,
            doc_id,
            get_settings().model.doc_structure_model,
            structure_payload,
            structure_result,
            structure_error,
        )

    stats = DocumentParseStats(
        node_count=len(nodes),
        line_count=len(markdown.splitlines()),
        content_length=len(markdown),
    )

    return DocumentParseResponse(
        doc_id=doc_id,
        title=title,
        file_name=file_name,
        markdown=markdown if include_markdown else None,
        structure_result=structure_result,
        structure_error=structure_error,
        nodes=nodes,
        stats=stats,
    )
# endregion
# ============================================
