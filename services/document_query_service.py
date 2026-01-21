"""
描述: 文档结构化查询服务
主要功能:
    - 查询结构化 JSON
    - 构建节点树
依赖: psycopg
"""

from __future__ import annotations

import json
from datetime import datetime

from psycopg import Connection

from schemas.document import DocumentStructureResponse, DocumentTreeNode


# ============================================
# region get_document_structure
# ============================================
def get_document_structure(conn: Connection, doc_id: int) -> DocumentStructureResponse | None:
    """
    获取文档结构化结果

    参数:
        conn: 数据库连接
        doc_id: 文档ID
    返回:
        结构化响应或 None
    """

    row = conn.execute(
        """
        SELECT doc_id, structure_model, structure_payload, structure_raw,
               structure_error, structure_created_at
        FROM document_nodes
        WHERE doc_id = %s AND parent_id IS NULL
        ORDER BY COALESCE(order_index, 0), node_id
        LIMIT 1
        """,
        (doc_id,),
    ).fetchone()

    if not row:
        return None

    payload = row[2]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = None

    created_at = row[5].isoformat() if isinstance(row[5], datetime) else None
    return DocumentStructureResponse(
        doc_id=row[0],
        model_name=row[1],
        payload=payload,
        raw_text=row[3],
        error=row[4],
        created_at=created_at,
    )
# endregion
# ============================================


# ============================================
# region get_document_tree
# ============================================
def get_document_tree(conn: Connection, doc_id: int) -> DocumentTreeNode | None:
    """
    构建文档节点树

    参数:
        conn: 数据库连接
        doc_id: 文档ID
    返回:
        文档树节点
    """

    rows = conn.execute(
        """
        SELECT node_id, parent_id, level, title, content
        FROM document_nodes
        WHERE doc_id = %s
        ORDER BY order_index
        """,
        (doc_id,),
    ).fetchall()

    if not rows:
        return None

    nodes: dict[int, DocumentTreeNode] = {}
    children_map: dict[int | None, list[int]] = {}
    for row in rows:
        node_id = int(row[0])
        parent_id = row[1]
        parent_id = int(parent_id) if parent_id is not None else None
        nodes[node_id] = DocumentTreeNode(
            title=row[3] or "Section",
            level=int(row[2]) if row[2] is not None else 0,
            content=row[4] or "",
            children=[],
        )
        children_map.setdefault(parent_id, []).append(node_id)

    def attach_children(node_id: int) -> None:
        node = nodes[node_id]
        child_ids = children_map.get(node_id, [])
        for child_id in child_ids:
            attach_children(child_id)
            node.children.append(nodes[child_id])

    root_ids = children_map.get(None, [])
    for root_id in root_ids:
        attach_children(root_id)

    if len(root_ids) == 1:
        return nodes[root_ids[0]]

    title_row = conn.execute(
        """
        SELECT title FROM documents WHERE doc_id = %s
        """,
        (doc_id,),
    ).fetchone()
    root_title = title_row[0] if title_row and title_row[0] else "Document"

    root = DocumentTreeNode(title=root_title, level=0, content="", children=[])
    for root_id in root_ids:
        root.children.append(nodes[root_id])
    return root
# endregion
# ============================================
