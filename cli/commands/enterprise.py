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

# ============================================
# region _get_db_url
# ============================================
def _get_db_url(ctx: typer.Context) -> str:
    db_url = ctx.obj.get("db_url") if ctx.obj else None
    if not db_url:
        raise typer.BadParameter("Database URL is required")
    return db_url
# endregion
# ============================================

# ============================================
# region import_enterprises
# ============================================
@app.command("import")
def import_enterprises(
    ctx: typer.Context,
    file_path: str = typer.Option(..., "--file", help="JSON 文件路径"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    批量导入企业信息

    参数:
        ctx: Typer 上下文
        file_path: JSON 文件路径
        json_output: 是否输出 JSON
    返回:
        None
    """

    with open(file_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise typer.BadParameter("JSON must be a list of objects")

    now = datetime.utcnow()
    payloads = []
    for item in data:
        if not isinstance(item, dict):
            raise typer.BadParameter("Each item must be an object")
        credit_code = item.get("credit_code")
        company_name = item.get("company_name")
        if not credit_code or not company_name:
            raise typer.BadParameter("credit_code and company_name are required")
        payloads.append(
            {
                "credit_code": normalize_commas(str(credit_code)),
                "company_name": company_name,
                "business_scope": item.get("business_scope"),
                "industry": item.get("industry"),
                "enterprise_type": item.get("enterprise_type"),
                "created_at": now,
                "updated_at": now,
            }
        )

    db_url = _get_db_url(ctx)
    with get_connection(db_url) as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
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
                VALUES (
                    %(credit_code)s,
                    %(company_name)s,
                    %(business_scope)s,
                    %(industry)s,
                    %(enterprise_type)s,
                    %(created_at)s,
                    %(updated_at)s
                )
                """,
                payloads,
            )

    result = {"inserted": len(payloads)}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Enterprises imported: {len(payloads)}")
# endregion
# ============================================


# ============================================
# region export_enterprises
# ============================================
@app.command("export")
def export_enterprises(
    ctx: typer.Context,
    out_path: str = typer.Option(..., "--out", help="输出 JSON 文件"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    导出企业信息

    参数:
        ctx: Typer 上下文
        out_path: 输出 JSON 文件
        json_output: 是否输出 JSON
    返回:
        None
    """

    db_url = _get_db_url(ctx)
    with get_connection(db_url) as conn:
        rows = conn.execute(
            """
            SELECT credit_code, company_name, business_scope, industry, enterprise_type,
                   created_at, updated_at
            FROM enterprises
            ORDER BY credit_code
            """
        ).fetchall()

    data = [
        {
            "credit_code": row[0],
            "company_name": row[1],
            "business_scope": row[2],
            "industry": row[3],
            "enterprise_type": row[4],
            "created_at": row[5],
            "updated_at": row[6],
        }
        for row in rows
    ]

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, default=str, indent=2)

    result = {"exported": len(data), "file": out_path}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Enterprises exported: {len(data)}")
# endregion
# ============================================

# ============================================
# region delete_enterprise
# ============================================
@app.command("delete")
def delete_enterprise(
    ctx: typer.Context,
    credit_code: str = typer.Option(..., help="统一社会信用代码"),
    confirm: bool = typer.Option(False, "--yes", help="跳过确认"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    删除企业信息

    参数:
        ctx: Typer 上下文
        credit_code: 统一社会信用代码
        json_output: 是否输出 JSON
    返回:
        None
    """

    if not confirm:
        confirmed = typer.confirm("确认删除企业？")
        if not confirmed:
            raise typer.Exit(code=1)

    db_url = _get_db_url(ctx)
    with get_connection(db_url) as conn:
        row = conn.execute(
            """
            DELETE FROM enterprises
            WHERE credit_code = %s
            RETURNING credit_code
            """,
            (credit_code,),
        ).fetchone()

    if not row:
        raise typer.Exit(code=1)

    result = {"credit_code": row[0], "deleted": True}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo("Enterprise deleted")
# endregion
# ============================================
# ============================================
# region insert_enterprise
# ============================================
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
# endregion
# ============================================

# ============================================
# region get_enterprise
# ============================================
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
# endregion
# ============================================
