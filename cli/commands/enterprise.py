"""
描述: 企业信息 CLI
主要功能:
    - 企业信息写入
    - 企业信息查询
依赖: typer, psycopg
"""

from __future__ import annotations

import json
from datetime import datetime

import typer

from cli.db import get_connection
from cli.validation import normalize_commas

app = typer.Typer(help="Enterprise data commands")


def _get_db_url(ctx: typer.Context) -> str:
    db_url = ctx.obj.get("db_url") if ctx.obj else None
    if not db_url:
        raise typer.BadParameter("Database URL is required")
    return db_url


@app.command("insert")
def insert_enterprise(
    ctx: typer.Context,
    credit_code: str = typer.Option(..., help="统一社会信用代码"),
    company_name: str = typer.Option(..., help="企业名称"),
    business_scope: str | None = typer.Option(None, help="经营范围"),
    industry: str | None = typer.Option(None, help="所属行业"),
    enterprise_type: str | None = typer.Option(None, help="企业类型"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    插入企业信息

    参数:
        ctx: Typer 上下文
        credit_code: 统一社会信用代码
        company_name: 企业名称
        business_scope: 经营范围
        industry: 所属行业
        enterprise_type: 企业类型
        json_output: 是否输出 JSON
    返回:
        None
    """

    db_url = _get_db_url(ctx)
    payload = {
        "credit_code": normalize_commas(credit_code),
        "company_name": company_name,
        "business_scope": business_scope,
        "industry": industry,
        "enterprise_type": enterprise_type,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    with get_connection(db_url) as conn:
        conn.execute(
            """
            INSERT INTO enterprises (
                credit_code,
                company_name,
                business_scope,
                industry,
                enterprise_type,
                created_at,
                updated_at
            )
            VALUES (%(credit_code)s, %(company_name)s, %(business_scope)s, %(industry)s,
                    %(enterprise_type)s, %(created_at)s, %(updated_at)s)
            """,
            payload,
        )

    if json_output:
        typer.echo(json.dumps({"status": "ok", **payload}, default=str))
    else:
        typer.echo("Enterprise inserted")


@app.command("get")
def get_enterprise(
    ctx: typer.Context,
    credit_code: str = typer.Option(..., help="统一社会信用代码"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    查询企业信息

    参数:
        ctx: Typer 上下文
        credit_code: 统一社会信用代码
        json_output: 是否输出 JSON
    返回:
        None
    """

    db_url = _get_db_url(ctx)
    with get_connection(db_url) as conn:
        row = conn.execute(
            """
            SELECT credit_code, company_name, business_scope, industry, enterprise_type,
                   created_at, updated_at
            FROM enterprises
            WHERE credit_code = %s
            """,
            (credit_code,),
        ).fetchone()

    if not row:
        raise typer.Exit(code=1)

    result = {
        "credit_code": row[0],
        "company_name": row[1],
        "business_scope": row[2],
        "industry": row[3],
        "enterprise_type": row[4],
        "created_at": row[5],
        "updated_at": row[6],
    }

    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Enterprise: {result['company_name']}")
