"""
描述: 甲方字段批量回填
主要功能:
    - 从正文抽取甲方
    - 文件名兜底
依赖: psycopg
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import get_settings
from db.connection import get_connection
from services.model_service import extract_json


def build_document_text(conn, doc_id: int, max_chars: int) -> str:
    rows = conn.execute(
        """
        SELECT title, content
        FROM document_nodes
        WHERE doc_id = %s
        ORDER BY order_index
        """,
        (doc_id,),
    ).fetchall()

    parts = [row[1] for row in rows if row[1]]
    if not parts:
        parts = [row[0] for row in rows if row[0]]

    text = "\n\n".join(parts)
    return text[:max_chars]


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        lines = stripped.splitlines()
        if lines and lines[0].lower().startswith("json"):
            stripped = "\n".join(lines[1:])
    return stripped.strip()


def extract_party_a_from_text(markdown: str, file_name: str | None) -> tuple[str | None, str | None]:
    prompt = (
        "从合同文本中抽取甲方全称，仅返回JSON。"
        "格式: {\"party_a_name\": \"...\"}. "
        "如果无法识别，返回空字符串。"
    )
    try:
        response = extract_json(f"{prompt}\n\n{markdown}")
        if response.content:
            json_text = _extract_json_text(response.content)
            payload = json.loads(json_text)
            if isinstance(payload, dict):
                name = str(payload.get("party_a_name") or "").strip()
                if name:
                    return name, "content"
    except Exception:
        pass

    if file_name:
        name = Path(file_name).stem.strip()
        return (name if name else None), "filename"

    return None, None


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill party_a_name")
    parser.add_argument("--limit", type=int, default=0, help="处理条数，0 为全部")
    parser.add_argument("--max-chars", type=int, default=6000, help="正文截断长度")
    parser.add_argument("--force", action="store_true", help="强制重跑所有文档")
    args = parser.parse_args()

    load_dotenv()
    db_url = get_settings().service.database_url

    with get_connection(db_url) as conn:
        if args.force:
            rows = conn.execute(
                """
                SELECT doc_id, file_name
                FROM documents
                ORDER BY doc_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT doc_id, file_name
                FROM documents
                WHERE party_a_name IS NULL OR party_a_name = ''
                ORDER BY doc_id
                """
            ).fetchall()

        if args.limit:
            rows = rows[: args.limit]

        updated = 0
        for doc_id, file_name in rows:
            text = build_document_text(conn, doc_id, args.max_chars)
            if text:
                party_a_name, source = extract_party_a_from_text(text, file_name)
            else:
                party_a_name = Path(file_name).stem if file_name else None
                source = "filename" if party_a_name else None

            party_a_credit_code = None

            conn.execute(
                """
                UPDATE documents
                SET party_a_name = %s,
                    party_a_credit_code = %s,
                    party_a_source = %s
                WHERE doc_id = %s
                """,
                (party_a_name, party_a_credit_code, source, doc_id),
            )
            updated += 1

        conn.commit()

    print(f"updated: {updated}")


if __name__ == "__main__":
    main()
