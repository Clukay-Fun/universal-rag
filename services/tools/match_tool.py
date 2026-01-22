"""
描述: 智能匹配工具
依赖: matching_service, tool_registry
"""
from __future__ import annotations

import os
from psycopg import connect
from services.matching_service import execute_matching
from services.tool_registry import BaseTool, register_tool
from pydantic import Field

@register_tool
class MatchTenderTool(BaseTool):
    """
    智能匹配工具
    
    用于根据招标需求ID，自动匹配知识库中最合适的业绩合同。
    """
    name: str = "match_tender"
    description: str = "根据招标需求ID匹配相关业绩。返回匹配得分最高的合同列表。"
    tender_id: int = Field(..., description="招标需求ID (Integer)")
    top_k: int = Field(5, description="返回结果数量")

    def run(self, **kwargs) -> str:
        tender_id = kwargs.get("tender_id") or self.tender_id
        top_k = kwargs.get("top_k") or self.top_k
        
        if not tender_id:
            return "Error: tender_id is missing."
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return "Error: DATABASE_URL not configured."

        try:
            with connect(db_url) as conn:
                # 获取招标需求 constraints (简单起见，execute_matching 内部并未重新查 constraints，
                # 但 execute_matching 签名是 (conn, tender_id, constraints, top_k)
                # 等等，execute_matching 需要 constraints 字典作为输入。
                # 工具应该先 fetch tender 拿到 constraints 吗？
                # 让我们检查 execute_matching 的定义。
                
                # 重新查看 execute_matching 签名：
                # def execute_matching(conn: Connection, tender_id: int, constraints: dict[str, Any], top_k: int = 10)
                
                # 所以我需要先获取 Tender 的 constraints。
                # 可以调用 tender_service.get_tender
                from services.tender_service import get_tender
                tender = get_tender(conn, tender_id)
                if not tender:
                    return f"Error: Tender {tender_id} not found."
                
                results = execute_matching(conn, tender_id, tender.constraints, top_k)
                
                # 格式化输出
                output = []
                for res in results.items:
                    output.append(f"- Match ID: {res.match_id}, Score: {res.score:.4f}, Contract: {res.party_a} ({res.contract_id})")
                    if res.reasons:
                        reasons_str = ", ".join(res.reasons[:3])
                        output.append(f"  Reasons: {reasons_str}")
                
                if not output:
                    return "No matching contracts found."
                    
                return "\n".join(output)

        except Exception as e:
            return f"Error executing matching: {str(e)}"
