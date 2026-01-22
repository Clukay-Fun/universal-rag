"""
描述: Agent 核心服务
主要功能:
    - 执行 Agent Loop (Think-Act-Observe)
    - 工具调用与结果处理
    - SSE 流式状态推送
依赖: model_service, tool_registry, sse_utils
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator

from services.model_service import chat
from services.sse_utils import AgentState, sse_status, sse_chunk, sse_error, sse_done
from services.tool_registry import ToolRegistry
# Ensure tools are registered
import services.tools  # noqa

logger = logging.getLogger(__name__)

# ============================================
# region Helper Functions
# ============================================
def _load_system_prompt() -> str:
    # 动态加载所有工具的 Schema
    schemas = ToolRegistry.get_all_schemas()
    schema_json = json.dumps(schemas, ensure_ascii=False, indent=2)
    
    try:
        with open("prompts/agent/system.md", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        # Fallback template
        template = "You are a helpful assistant. Tools: {tool_schemas}"
    
    return template.replace("{tool_schemas}", schema_json)

def _parse_tool_call(content: str) -> dict[str, Any] | None:
    """
    尝试从内容中解析 JSON 工具调用
    支持直接 JSON 或 Markdown 代码块 ```json ... ```
    """
    content = content.strip()
    
    # 尝试匹配 Markdown code block
    json_block = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if json_block:
        text = json_block.group(1)
    else:
        text = content
        
    # 尝试解析 JSON
    try:
        # 简单清洗
        if text.startswith("```"): text = text.strip("`").strip()
        if text.startswith("json"): text = text[4:].strip()
        
        data = json.loads(text)
        if isinstance(data, dict) and "tool" in data and "args" in data:
            return data
    except json.JSONDecodeError:
        pass
        
    return None
# endregion
# ============================================


# ============================================
# region run_agent_loop
# ============================================
async def run_agent_loop(
    session_id: str,
    user_content: str,
    history: list[dict[str, str]], # 上下文历史
    max_steps: int = 10
) -> AsyncGenerator[str, None]:
    """
    执行 Agent 思考-行动循环
    
    Args:
        session_id: 会话ID
        user_content: 用户最新输入
        history: 历史消息列表 [{"role": "user", "content": ...}, ...]
    """
    
    # 1. 初始化
    system_prompt = _load_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    
    current_step = 0
    final_answer = ""
    last_tool_signature = None
    
    yield sse_status(AgentState.THINKING, step=1, total=max_steps, message="思考中...")

    while current_step < max_steps:
        current_step += 1
        
        try:
            # 2. 调用 LLM (Reasoning)
            # 注意：这是一个同步调用，如果用 uvicorn 运行，建议放在线程池中，但这里简化直接调用
            response = chat(messages)
            content = response.content or ""
            
            # 3. 解析输出
            tool_call = _parse_tool_call(content)
            
            if tool_call:
                # === 工具调用分支 ===
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args") or {}
                
                # 检查死循环
                tool_signature = json.dumps({"tool": tool_name, "args": tool_args}, sort_keys=True)
                if tool_signature == last_tool_signature:
                    # 发现重复调用，强制终止或给予强烈提示
                    error_msg = f"Error: Repeated tool call '{tool_name}' with same arguments. Stop and answer."
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": error_msg})
                    yield sse_status(AgentState.ERROR, step=current_step, total=max_steps, message="检测到重复调用")
                    # 选择继续让模型有机会纠正其实有点冒险，不如直接抛异常返回。
                    # 为了用户体验，我们让它作为 Tool Result 返回，但如果这是第N次...
                    # 简单点，直接让模型看到错误
                    # 更新 last_tool_signature 以避免在此处卡死（如果模型换了参数则可以）
                    # 但为了防止无限发错误消息，我们还是 sleep 一下
                    await asyncio.sleep(1)
                    continue

                last_tool_signature = tool_signature
                
                yield sse_status(
                    AgentState.EXECUTING, 
                    step=current_step, 
                    total=max_steps, 
                    message=f"调用工具: {tool_name}"
                )
                
                # 查找工具
                tool_cls = ToolRegistry.get_tool(tool_name)
                if not tool_cls:
                    result = f"Error: Tool '{tool_name}' not found."
                else:
                    try:
                        # 实例化并运行
                        tool_instance = tool_cls(**tool_args)
                        # TODO: run 可能是同步或异步，BaseTool 定义是同步的
                        result = tool_instance.run()
                    except Exception as e:
                        result = f"Error execution tool: {str(e)}"
                
                # 将工具调用和结果追加到历史
                # 注意：为了让模型知道它刚才做了什么，我们需要把它的思考（content）加入历史
                # 并且把工具结果作为 role="tool" (或者 user) 加入
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",  # 使用 user 模拟 observatory 结果，或者如果模型支持 tool role
                    "content": f"Tool '{tool_name}' Result: {result}"
                })
                
                # 继续循环
                result_preview = str(result)[:50].replace("\n", " ")
                yield sse_status(AgentState.THINKING, step=current_step+1, total=max_steps, message=f"工具返回: {result_preview}...")
                
                # 防止请求过快
                await asyncio.sleep(1)
                continue
                
            else:
                # === 最终回答分支 ===
                # 不是工具调用，直接作为回答输出
                final_answer = content
                yield sse_status(AgentState.DONE, step=current_step, total=max_steps, message="已完成")
                yield sse_chunk(final_answer)
                # yield sse_done() -> 由 API 层发送
                return

        except Exception as e:
            logger.error(f"Agent loop error: {e}", exc_info=True)
            yield sse_error(f"Agent execution failed: {str(e)}")
            return
    
    # 超过最大步数
    yield sse_error("Task limit exceeded (Max steps reached).")
# endregion
# ============================================
