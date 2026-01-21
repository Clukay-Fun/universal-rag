"""
描述: 节点路径重建脚本
主要功能:
    - 回填 document_nodes.path
依赖: psycopg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import get_settings
from db.connection import get_connection
from services.document_path_service import rebuild_node_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild document node paths")
    parser.add_argument("--doc-id", type=int, default=0, help="指定文档ID")
    args = parser.parse_args()

    load_dotenv()
    db_url = get_settings().service.database_url

    with get_connection(db_url) as conn:
        doc_id = args.doc_id if args.doc_id > 0 else None
        docs, nodes = rebuild_node_paths(conn, doc_id)

    print(f"documents: {docs}, nodes: {nodes}")


if __name__ == "__main__":
    main()
