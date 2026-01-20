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
from decimal import Decimal
import typer

from cli.db import get_connection
from cli.validation import (
    ensure_non_negative,
    normalize_commas,
    parse_decimal,
    parse_sign_date,
)

app = typer.Typer(help="Performance data commands")

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
# region _parse_decimal_input
# ============================================
def _parse_decimal_input(value: object | None, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return parse_decimal(str(value), field_name)
# endregion
# ============================================

# ============================================
# region delete_performance
# ============================================
@app.command("delete")
def delete_performance(
    ctx: typer.Context,
    record_id: int = typer.Option(..., "--id", help="主键ID"),
    confirm: bool = typer.Option(False, "--yes", help="跳过确认"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    删除业绩记录

    参数:
        ctx: Typer 上下文
        record_id: 主键ID
        confirm: 是否跳过确认
        json_output: 是否输出 JSON
    返回:
        None
    """

    if not confirm:
        confirmed = typer.confirm("确认删除业绩？")
        if not confirmed:
            raise typer.Exit(code=1)

    with get_connection(_get_db_url(ctx)) as conn:
        row = conn.execute(
            """
            DELETE FROM performances
            WHERE id = %s
            RETURNING id
            """,
            (record_id,),
        ).fetchone()

    if not row:
        raise typer.Exit(code=1)

    result = {"id": row[0], "deleted": True}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo("Performance deleted")
# endregion
# ============================================

# ============================================
# region import_performances
# ============================================
@app.command("import")
def import_performances(
    ctx: typer.Context,
    file_path: str = typer.Option(..., "--file", help="JSON 文件路径"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    批量导入业绩记录

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
    errors: list[dict[str, object]] = []
    for index, item in enumerate(data):
        try:
            if not isinstance(item, dict):
                raise ValueError("Each item must be an object")

            record_id = item.get("id")
            amount_value = _parse_decimal_input(item.get("amount"), "amount")
            if record_id is None or amount_value is None:
                raise ValueError("id and amount are required")

            subject_amount_value = _parse_decimal_input(
                item.get("subject_amount"), "subject_amount"
            )
            ensure_non_negative(amount_value, "amount")
            if subject_amount_value is not None:
                ensure_non_negative(subject_amount_value, "subject_amount")

            sign_date_raw = item.get("sign_date_raw")
            sign_date_norm = item.get("sign_date_norm")
            raw_value = str(sign_date_raw) if sign_date_raw is not None else None
            norm_value = str(sign_date_norm) if sign_date_norm is not None else None
            sign_date_raw, sign_date_norm_date = parse_sign_date(raw_value, norm_value)

            payloads.append(
                {
                    "id": int(record_id),
                    "file_name": item.get("file_name"),
                    "party_a": normalize_commas(item.get("party_a")),
                    "party_a_id": normalize_commas(item.get("party_a_id")),
                    "contract_number": item.get("contract_number"),
                    "amount": amount_value,
                    "fee_method": item.get("fee_method"),
                    "sign_date_norm": sign_date_norm_date,
                    "sign_date_raw": sign_date_raw,
                    "project_type": item.get("project_type"),
                    "project_detail": item.get("project_detail"),
                    "subject_amount": subject_amount_value,
                    "opponent": item.get("opponent"),
                    "team_member": normalize_commas(item.get("team_member")),
                    "summary": None,
                    "image_data": None,
                    "image_count": item.get("image_count"),
                    "raw_text": item.get("raw_text"),
                    "created_at": now,
                    "updated_at": now,
                    "embedding": None,
                }
            )
        except Exception as exc:
            errors.append({"index": index, "error": str(exc)})

    if payloads:
        with get_connection(_get_db_url(ctx)) as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
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
                    payloads,
                )

    result = {"inserted": len(payloads), "failed": len(errors), "errors": errors}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Performances imported: {len(payloads)}")
        if errors:
            for error in errors:
                typer.echo(f"Error[{error['index']}]: {error['error']}")

    if errors:
        raise typer.Exit(code=1)
# endregion
# ============================================


# ============================================
# region export_performances
# ============================================
@app.command("export")
def export_performances(
    ctx: typer.Context,
    out_path: str = typer.Option(..., "--out", help="输出 JSON 文件"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    导出业绩记录

    参数:
        ctx: Typer 上下文
        out_path: 输出 JSON 文件
        json_output: 是否输出 JSON
    返回:
        None
    """

    with get_connection(_get_db_url(ctx)) as conn:
        rows = conn.execute(
            """
            SELECT id, file_name, party_a, party_a_id, contract_number, amount, fee_method,
                   sign_date_norm, sign_date_raw, project_type, project_detail, subject_amount,
                   opponent, team_member, summary, image_count, raw_text, created_at, updated_at
            FROM performances
            ORDER BY id
            """
        ).fetchall()

    data = [
        {
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
        for row in rows
    ]

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, default=str, indent=2)

    result = {"exported": len(data), "file": out_path}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Performances exported: {len(data)}")
# endregion
# ============================================
# ============================================
# region insert_performance
# ============================================
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
# endregion
# ============================================

# ============================================
# region get_performance
# ============================================
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
# endregion
# ============================================
