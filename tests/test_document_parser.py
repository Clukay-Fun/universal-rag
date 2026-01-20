"""
描述: 文档解析单元测试
主要功能:
    - Markdown 节点解析测试
依赖: unittest
"""

from __future__ import annotations

import unittest

from services.document_service import parse_markdown_nodes


class DocumentParserTests(unittest.TestCase):
    """
    文档解析测试
    """

    # ============================================
    # region test_parse_headings
    # ============================================
    def test_parse_headings(self) -> None:
        markdown = "# Title\nIntro\n## Sub\nSub content"
        nodes = parse_markdown_nodes(markdown)
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].title, "Title")
        self.assertEqual(nodes[0].content, "Intro")
        self.assertEqual(nodes[1].title, "Sub")
        self.assertEqual(nodes[1].parent_id, nodes[0].node_id)
    # endregion
    # ============================================

    # ============================================
    # region test_parse_without_headings
    # ============================================
    def test_parse_without_headings(self) -> None:
        markdown = "Line one\nLine two"
        nodes = parse_markdown_nodes(markdown)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].title, "Document")
        self.assertEqual(nodes[0].content, "Line one\nLine two")
    # endregion
    # ============================================


if __name__ == "__main__":
    unittest.main()
