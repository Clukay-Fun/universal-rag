"""
描述: 智能匹配 CLI
主要功能:
    - 招标需求创建与查询
    - 执行匹配与结果查询
依赖: typer, psycopg
"""

from __future__ import annotations

import json
import typer

from cli.db import get_connection
from services.matching_service import (
    delete_match_results,
    execute_matching,
    get_match_results,
)
from services.tender_service import (
    create_tender_requirement,
    delete_tender_requirement,
    get_tender_requirement,
    list_tender_requirements,
    parse_tender_constraints,
)
from schemas.matching import TenderRequirementCreate

app = typer.Typer(help="智能匹配命令")


# ============================================
# region 获取数据库URL
# ============================================
def _get_db_url(ctx: typer.Context) -> str:
    """获取数据库连接URL"""
    db_url = ctx.obj.get("db_url") if ctx.obj else None
    if not db_url:
        raise typer.BadParameter("数据库URL未配置")
    return db_url
# endregion
# ============================================


# ============================================
# region 创建招标需求
# ============================================
@app.command("create")
def create_tender(
    ctx: typer.Context,
    title: str | None = typer.Option(None, "--title", help="招标标题"),
    raw_text: str = typer.Option(..., "--text", help="招标原文"),
    auto_parse: bool = typer.Option(True, "--parse/--no-parse", help="是否自动解析约束"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    创建招标需求

    参数:
        ctx: Typer 上下文
        title: 招标标题
        raw_text: 招标原文
        auto_parse: 是否自动解析约束条件
        json_output: 是否输出 JSON
    返回:
        None
    """
    data = TenderRequirementCreate(title=title, raw_text=raw_text)

    with get_connection(_get_db_url(ctx)) as conn:
        result = create_tender_requirement(conn, data, auto_parse=auto_parse)

    output = {
        "tender_id": result.tender_id,
        "title": result.title,
        "constraints": result.constraints,
        "created_at": str(result.created_at),
    }

    if json_output:
        typer.echo(json.dumps(output, ensure_ascii=False, default=str))
    else:
        typer.echo(f"招标需求已创建: ID={result.tender_id}")
        if result.constraints:
            typer.echo(f"解析约束: {json.dumps(result.constraints, ensure_ascii=False)}")
# endregion
# ============================================


# ============================================
# region 查询招标需求
# ============================================
@app.command("get")
def get_tender(
    ctx: typer.Context,
    tender_id: int = typer.Option(..., "--id", help="招标需求ID"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    查询招标需求详情

    参数:
        ctx: Typer 上下文
        tender_id: 招标需求ID
        json_output: 是否输出 JSON
    返回:
        None
    """
    with get_connection(_get_db_url(ctx)) as conn:
        result = get_tender_requirement(conn, tender_id)

    if not result:
        typer.echo("招标需求不存在", err=True)
        raise typer.Exit(code=1)

    output = {
        "tender_id": result.tender_id,
        "title": result.title,
        "raw_text": result.raw_text,
        "constraints": result.constraints,
        "created_at": str(result.created_at),
    }

    if json_output:
        typer.echo(json.dumps(output, ensure_ascii=False, default=str))
    else:
        typer.echo(f"招标需求 ID={result.tender_id}")
        typer.echo(f"标题: {result.title}")
        typer.echo(f"约束: {json.dumps(result.constraints, ensure_ascii=False)}")
# endregion
# ============================================


# ============================================
# region 招标需求列表
# ============================================
@app.command("list")
def list_tenders(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", help="返回数量"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    查询招标需求列表

    参数:
        ctx: Typer 上下文
        limit: 返回数量
        json_output: 是否输出 JSON
    返回:
        None
    """
    with get_connection(_get_db_url(ctx)) as conn:
        results = list_tender_requirements(conn, limit=limit)

    output = [
        {
            "tender_id": r.tender_id,
            "title": r.title,
            "created_at": str(r.created_at),
        }
        for r in results
    ]

    if json_output:
        typer.echo(json.dumps(output, ensure_ascii=False, default=str))
    else:
        typer.echo(f"共 {len(results)} 条招标需求:")
        for r in results:
            typer.echo(f"  [{r.tender_id}] {r.title or '(无标题)'}")
# endregion
# ============================================


# ============================================
# region 删除招标需求
# ============================================
@app.command("delete")
def delete_tender(
    ctx: typer.Context,
    tender_id: int = typer.Option(..., "--id", help="招标需求ID"),
    confirm: bool = typer.Option(False, "--yes", help="跳过确认"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    删除招标需求

    参数:
        ctx: Typer 上下文
        tender_id: 招标需求ID
        confirm: 是否跳过确认
        json_output: 是否输出 JSON
    返回:
        None
    """
    if not confirm:
        confirmed = typer.confirm(f"确认删除招标需求 {tender_id}？")
        if not confirmed:
            raise typer.Exit(code=1)

    with get_connection(_get_db_url(ctx)) as conn:
        result = delete_tender_requirement(conn, tender_id)

    if result is None:
        typer.echo("招标需求不存在", err=True)
        raise typer.Exit(code=1)

    output = {"tender_id": result, "deleted": True}

    if json_output:
        typer.echo(json.dumps(output, default=str))
    else:
        typer.echo(f"招标需求 {result} 已删除")
# endregion
# ============================================


# ============================================
# region 执行匹配
# ============================================
from services.matching_service import execute_matching_stream


@app.command("match")
def match_tender(
    ctx: typer.Context,
    tender_id: int = typer.Option(..., "--id", help="招标需求ID"),
    top_k: int = typer.Option(10, "--top", help="返回前K条结果"),
    stream: bool = typer.Option(False, "--stream", help="启用实时进度显示"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    执行匹配：筛选业绩 + 评分 + 排序

    参数:
        ctx: Typer 上下文
        tender_id: 招标需求ID
        top_k: 返回前K条结果
        stream: 是否启用实时进度显示
        json_output: 是否输出 JSON
    返回:
        None
    """
    with get_connection(_get_db_url(ctx)) as conn:
        # 1. 获取招标需求
        tender = get_tender_requirement(conn, tender_id)
        if not tender:
            typer.echo("招标需求不存在", err=True)
            raise typer.Exit(code=1)

        # 2. 清除旧结果
        delete_match_results(conn, tender_id)

        # 3. 执行匹配
        if stream:
            # 流式模式：实时显示进度
            typer.echo(f"开始匹配招标需求 {tender_id}...", err=True)
            try:
                gen = execute_matching_stream(conn, tender_id, tender.constraints, top_k=top_k)
                results = []
                for event in gen:
                    # 解析 SSE 事件并显示
                    if event.startswith("event: status"):
                        # 提取状态信息
                        lines = event.strip().split("\n")
                        for line in lines:
                            if line.startswith("data:"):
                                data = json.loads(line[5:].strip())
                                state = data.get("state", "")
                                message = data.get("message", "")
                                typer.echo(f"  [{state}] {message}", err=True)
                    elif event.startswith("event: progress"):
                        lines = event.strip().split("\n")
                        for line in lines:
                            if line.startswith("data:"):
                                data = json.loads(line[5:].strip())
                                percent = data.get("percent", 0)
                                message = data.get("message", "")
                                typer.echo(f"  进度: {percent:.1f}% - {message}", err=True)
                    elif event.startswith("event: done"):
                        lines = event.strip().split("\n")
                        for line in lines:
                            if line.startswith("data:"):
                                data = json.loads(line[5:].strip())
                                results = data.get("results", [])
            except Exception as exc:
                typer.echo(f"匹配失败: {exc}", err=True)
                raise typer.Exit(code=1)

            if json_output:
                typer.echo(json.dumps(results, ensure_ascii=False, default=str))
            else:
                typer.echo(f"\n匹配完成，共 {len(results)} 条结果")
        else:
            # 普通模式
            typer.echo(f"正在匹配招标需求 {tender_id}...", err=True)
            try:
                results = execute_matching(conn, tender_id, tender.constraints, top_k=top_k)
            except Exception as exc:
                typer.echo(f"匹配失败: {exc}", err=True)
                raise typer.Exit(code=1)

            output = [
                {
                    "match_id": r.match_id,
                    "contract_id": r.contract_id,
                    "score": float(r.score),
                    "reasons": r.reasons,
                }
                for r in results
            ]

            if json_output:
                typer.echo(json.dumps(output, ensure_ascii=False, default=str))
            else:
                typer.echo(f"匹配完成，共 {len(results)} 条结果:")
                for r in results:
                    typer.echo(f"  [{r.contract_id}] 得分: {r.score:.2f}")
                    for reason in r.reasons[:2]:
                        typer.echo(f"    - {reason}")
# endregion
# ============================================


# ============================================
# region 查询匹配结果
# ============================================
@app.command("results")
def get_results(
    ctx: typer.Context,
    tender_id: int = typer.Option(..., "--id", help="招标需求ID"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    查询匹配结果（带业绩详情）

    参数:
        ctx: Typer 上下文
        tender_id: 招标需求ID
        json_output: 是否输出 JSON
    返回:
        None
    """
    with get_connection(_get_db_url(ctx)) as conn:
        result = get_match_results(conn, tender_id)

    output = {
        "tender_id": result.tender_id,
        "total": result.total,
        "items": [
            {
                "match_id": item.match_id,
                "contract_id": item.contract_id,
                "score": float(item.score),
                "reasons": item.reasons,
                "party_a": item.party_a,
                "project_type": item.project_type,
                "project_detail": item.project_detail,
                "amount": float(item.amount) if item.amount else None,
            }
            for item in result.items
        ],
    }

    if json_output:
        typer.echo(json.dumps(output, ensure_ascii=False, default=str))
    else:
        typer.echo(f"招标需求 {tender_id} 的匹配结果，共 {result.total} 条:")
        for item in result.items:
            typer.echo(f"\n  [{item.contract_id}] 得分: {item.score:.2f}")
            typer.echo(f"    甲方: {item.party_a}")
            typer.echo(f"    类型: {item.project_type}")
            typer.echo(f"    金额: {item.amount} 万元")
            typer.echo("    理由:")
            for reason in item.reasons:
                typer.echo(f"      - {reason}")
# endregion
# ============================================


# ============================================
# region 解析招标约束（测试用）
# ============================================
@app.command("parse")
def parse_constraints(
    ctx: typer.Context,
    raw_text: str = typer.Option(..., "--text", help="招标原文"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    解析招标约束条件（仅测试，不保存）

    参数:
        ctx: Typer 上下文
        raw_text: 招标原文
        json_output: 是否输出 JSON
    返回:
        None
    """
    try:
        constraints = parse_tender_constraints(raw_text)
    except Exception as exc:
        typer.echo(f"解析失败: {exc}", err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(constraints, ensure_ascii=False, default=str))
    else:
        typer.echo("解析结果:")
        for key, value in constraints.items():
            typer.echo(f"  {key}: {value}")
# endregion
# ============================================
