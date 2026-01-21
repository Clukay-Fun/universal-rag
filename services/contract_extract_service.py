"""
描述: 合同信息抽取服务
主要功能:
    - 读取提示词
    - 调用模型提取合同字段
依赖: 标准库
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.model_service import extract_json

PROMPT_PATH = Path("prompts/contracts/contract_extract.md")


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
# region load_contract_prompt
# ============================================
def load_contract_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt not found: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")
# endregion
# ============================================


# ============================================
# region extract_contract_fields
# ============================================
def extract_contract_fields(markdown: str) -> dict[str, Any]:
    prompt = load_contract_prompt()
    response = extract_json(f"{prompt}\n\n{markdown}")
    if not response.content:
        raise ValueError("Empty model response")
    json_text = _extract_json_text(response.content)
    payload = json.loads(json_text)
    if not isinstance(payload, dict):
        raise ValueError("Contract extract response must be a JSON object")
    return payload
# endregion
# ============================================
