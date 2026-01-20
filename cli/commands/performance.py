"""
描述: 业绩/合同 CLI
主要功能:
    - 业绩写入
    - 业绩查询
依赖: typer, psycopg
"""

from __future__ import annotations

import json
from datetime import datetime
import typer

from cli.db import get_connection
from cli.validation import (
    ensure_non_negative,
    normalize_commas,
    parse_decimal,
    parse_sign_date,
)

app = typer.Typer(help="Performance data commands")


def _get_db_url(ctx: typer.Context) -> str:
    db_url = ctx.obj.get("db_url") if ctx.obj else None
    if not db_url:
        raise typer.BadParameter("Database URL is required")
    return db_url


@app.command("insert")
def insert_performance(
    ctx: typer.Context,
    record_id: int = typer.Option(..., "--id", help="主键ID"),
    file_name: str | None = typer.Option(None, help="文件名"),
    party_a: str | None = typer.Option(None, help="甲方名称（逗号分隔）"),
    party_a_id: str | None = typer.Option(None, help="甲方证件号（逗号分隔）"),
    contract_number: int | None = typer.Option(None, help="合同编号"),
    amount: str = typer.Option(..., help="金额（万元）"),
    fee_method: str | None = typer.Option(None, help="计费方式（原文）"),
    sign_date_raw: str | None = typer.Option(None, help="签署日期原文"),
    sign_date_norm: str | None = typer.Option(None, help="签署日期（YYYY-MM-DD）"),
    project_type: str | None = typer.Option(None, help="合同类型"),
    project_detail: str | None = typer.Option(None, help="项目详情"),
    subject_amount: str | None = typer.Option(None, help="标的金额（万元）"),
    opponent: str | None = typer.Option(None, help="相对方/对手方"),
    team_member: str | None = typer.Option(None, help="团队成员"),
    image_count: int | None = typer.Option(None, help="图片数量"),
    raw_text: str | None = typer.Option(None, help="原始文本"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    插入业绩记录

    参数:
        ctx: Typer 上下文
        record_id: 主键ID
        file_name: 文件名
        party_a: 甲方名称
        party_a_id: 甲方证件号
        contract_number: 合同编号
        amount: 合同金额
        fee_method: 计费方式原文
        sign_date_raw: 签署日期原文
        sign_date_norm: 标准化日期
        project_type: 合同类型
        project_detail: 项目详情
        subject_amount: 标的金额
        opponent: 相对方
        team_member: 团队成员
        image_count: 图片数量
        raw_text: 原始文本
        json_output: 是否输出 JSON
    返回:
        None
    """

    amount_decimal = parse_decimal(amount, "amount")
    ensure_non_negative(amount_decimal, "amount")

    subject_amount_decimal = None
    if subject_amount is not None:
        subject_amount_decimal = parse_decimal(subject_amount, "subject_amount")
        ensure_non_negative(subject_amount_decimal, "subject_amount")

    sign_date_raw, sign_date_norm_date = parse_sign_date(sign_date_raw, sign_date_norm)

    payload = {
        "id": record_id,
        "file_name": file_name,
        "party_a": normalize_commas(party_a),
        "party_a_id": normalize_commas(party_a_id),
        "contract_number": contract_number,
        "amount": amount_decimal,
        "fee_method": fee_method,
        "sign_date_raw": sign_date_raw,
        "sign_date_norm": sign_date_norm_date,
        "project_type": project_type,
        "project_detail": project_detail,
        "subject_amount": subject_amount_decimal,
        "opponent": opponent,
        "team_member": normalize_commas(team_member),
        "summary": None,
        "image_data": None,
        "image_count": image_count,
        "raw_text": raw_text,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "embedding": None,
    }

    with get_connection(_get_db_url(ctx)) as conn:
        conn.execute(
            """
            INSERT INTO performances (
                id,
                file_name,
                party_a,
                party_a_id,
                contract_number,
                amount,
                fee_method,
                sign_date_norm,
                sign_date_raw,
                project_type,
                project_detail,
                subject_amount,
                opponent,
                team_member,
                summary,
                image_data,
                image_count,
                raw_text,
                created_at,
                updated_at,
                embedding
            )
            VALUES (
                %(id)s,
                %(file_name)s,
                %(party_a)s,
                %(party_a_id)s,
                %(contract_number)s,
                %(amount)s,
                %(fee_method)s,
                %(sign_date_norm)s,
                %(sign_date_raw)s,
                %(project_type)s,
                %(project_detail)s,
                %(subject_amount)s,
                %(opponent)s,
                %(team_member)s,
                %(summary)s,
                %(image_data)s,
                %(image_count)s,
                %(raw_text)s,
                %(created_at)s,
                %(updated_at)s,
                %(embedding)s
            )
            """,
            payload,
        )

    if json_output:
        typer.echo(json.dumps({"status": "ok", **payload}, default=str))
    else:
        typer.echo("Performance inserted")


@app.command("get")
def get_performance(
    ctx: typer.Context,
    record_id: int = typer.Option(..., "--id", help="主键ID"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    查询业绩记录

    参数:
        ctx: Typer 上下文
        record_id: 主键ID
        json_output: 是否输出 JSON
    返回:
        None
    """

    with get_connection(_get_db_url(ctx)) as conn:
        row = conn.execute(
            """
            SELECT id, file_name, party_a, party_a_id, contract_number, amount, fee_method,
                   sign_date_norm, sign_date_raw, project_type, project_detail, subject_amount,
                   opponent, team_member, summary, image_count, raw_text, created_at, updated_at
            FROM performances
            WHERE id = %s
            """,
            (record_id,),
        ).fetchone()

    if not row:
        raise typer.Exit(code=1)

    result = {
        "id": row[0],
        "file_name": row[1],
        "party_a": row[2],
        "party_a_id": row[3],
        "contract_number": row[4],
        "amount": row[5],
        "fee_method": row[6],
        "sign_date_norm": row[7],
        "sign_date_raw": row[8],
        "project_type": row[9],
        "project_detail": row[10],
        "subject_amount": row[11],
        "opponent": row[12],
        "team_member": row[13],
        "summary": row[14],
        "image_count": row[15],
        "raw_text": row[16],
        "created_at": row[17],
        "updated_at": row[18],
    }

    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Performance: {result['id']}")
