"""
描述: 律师信息 CLI
主要功能:
    - 律师信息写入
    - 律师信息查询
    - 律师信息删除
依赖: typer, psycopg
"""

from __future__ import annotations

import json
from datetime import datetime

import typer

from cli.db import get_connection

app = typer.Typer(help="Lawyer data commands")


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
# region import_lawyers
# ============================================
@app.command("import")
def import_lawyers(
    ctx: typer.Context,
    file_path: str = typer.Option(..., "--file", help="JSON 文件路径"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    批量导入律师信息

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
            name = item.get("name")
            if record_id is None or not name:
                raise ValueError("id and name are required")

            embedding_value = item.get("resume_embedding")
            if isinstance(embedding_value, list):
                embedding_list = [float(v) for v in embedding_value]
            elif isinstance(embedding_value, str):
                embedding_list = _parse_embedding(embedding_value)
            elif embedding_value is None:
                embedding_list = None
            else:
                raise ValueError("resume_embedding must be list or string")

            payloads.append(
                {
                    "id": int(record_id),
                    "name": name,
                    "id_card": item.get("id_card"),
                    "license_no": item.get("license_no"),
                    "resume": item.get("resume"),
                    "resume_embedding": _format_vector(embedding_list),
                    "id_card_image": item.get("id_card_image"),
                    "degree_image": item.get("degree_image"),
                    "diploma_image": item.get("diploma_image"),
                    "license_image": item.get("license_image"),
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except Exception as exc:
            errors.append({"index": index, "error": str(exc)})

    if payloads:
        with get_connection(_get_db_url(ctx)) as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO lawyers (
                        id,
                        name,
                        id_card,
                        license_no,
                        resume,
                        resume_embedding,
                        id_card_image,
                        degree_image,
                        diploma_image,
                        license_image,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %(id)s,
                        %(name)s,
                        %(id_card)s,
                        %(license_no)s,
                        %(resume)s,
                        %(resume_embedding)s,
                        %(id_card_image)s,
                        %(degree_image)s,
                        %(diploma_image)s,
                        %(license_image)s,
                        %(created_at)s,
                        %(updated_at)s
                    )
                    """,
                    payloads,
                )

    result = {"inserted": len(payloads), "failed": len(errors), "errors": errors}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Lawyers imported: {len(payloads)}")
        if errors:
            for error in errors:
                typer.echo(f"Error[{error['index']}]: {error['error']}")

    if errors:
        raise typer.Exit(code=1)
# endregion
# ============================================


# ============================================
# region export_lawyers
# ============================================
@app.command("export")
def export_lawyers(
    ctx: typer.Context,
    out_path: str = typer.Option(..., "--out", help="输出 JSON 文件"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    导出律师信息

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
            SELECT id, name, id_card, license_no, resume, resume_embedding, id_card_image,
                   degree_image, diploma_image, license_image, created_at, updated_at
            FROM lawyers
            ORDER BY id
            """
        ).fetchall()

    data = [
        {
            "id": row[0],
            "name": row[1],
            "id_card": row[2],
            "license_no": row[3],
            "resume": row[4],
            "resume_embedding": _normalize_vector(row[5]),
            "id_card_image": row[6],
            "degree_image": row[7],
            "diploma_image": row[8],
            "license_image": row[9],
            "created_at": row[10],
            "updated_at": row[11],
        }
        for row in rows
    ]

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, default=str, indent=2)

    result = {"exported": len(data), "file": out_path}
    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Lawyers exported: {len(data)}")
# endregion
# ============================================

# ============================================
# region _parse_embedding
# ============================================
def _parse_embedding(value: str | None) -> list[float] | None:
    """
    解析向量字符串

    参数:
        value: 逗号分隔的向量
    返回:
        向量列表
    """

    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        return []
    return [float(item) for item in items]
# endregion
# ============================================


# ============================================
# region _format_vector
# ============================================
def _format_vector(values: list[float] | None) -> str | None:
    """
    转换为 pgvector 字面量

    参数:
        values: 向量列表
    返回:
        pgvector 字面量
    """

    if values is None:
        return None
    return f"[{','.join(str(float(v)) for v in values)}]"
# endregion
# ============================================


# ============================================
# region _normalize_vector
# ============================================
def _normalize_vector(value: object | None) -> list[float] | None:
    """
    规范化数据库向量

    参数:
        value: 数据库存储值
    返回:
        向量列表
    """

    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    if isinstance(value, str):
        text = value.strip().strip("[]")
        if not text:
            return []
        return [float(item) for item in text.split(",")]
    return None
# endregion
# ============================================


# ============================================
# region insert_lawyer
# ============================================
@app.command("insert")
def insert_lawyer(
    ctx: typer.Context,
    record_id: int = typer.Option(..., "--id", help="主键ID"),
    name: str = typer.Option(..., help="姓名"),
    id_card: str | None = typer.Option(None, help="身份证号"),
    license_no: str | None = typer.Option(None, help="执业证号"),
    resume: str | None = typer.Option(None, help="个人简介/简历"),
    resume_embedding: str | None = typer.Option(None, help="简历向量（逗号分隔）"),
    id_card_image: str | None = typer.Option(None, help="身份证照片路径"),
    degree_image: str | None = typer.Option(None, help="学位证照片路径"),
    diploma_image: str | None = typer.Option(None, help="毕业证照片路径"),
    license_image: str | None = typer.Option(None, help="执业证照片路径"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    插入律师信息

    参数:
        ctx: Typer 上下文
        record_id: 主键ID
        name: 姓名
        id_card: 身份证号
        license_no: 执业证号
        resume: 简历
        resume_embedding: 简历向量
        id_card_image: 身份证照片路径
        degree_image: 学位证照片路径
        diploma_image: 毕业证照片路径
        license_image: 执业证照片路径
        json_output: 是否输出 JSON
    返回:
        None
    """

    embedding_list = _parse_embedding(resume_embedding)
    payload = {
        "id": record_id,
        "name": name,
        "id_card": id_card,
        "license_no": license_no,
        "resume": resume,
        "resume_embedding": _format_vector(embedding_list),
        "id_card_image": id_card_image,
        "degree_image": degree_image,
        "diploma_image": diploma_image,
        "license_image": license_image,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    with get_connection(_get_db_url(ctx)) as conn:
        conn.execute(
            """
            INSERT INTO lawyers (
                id,
                name,
                id_card,
                license_no,
                resume,
                resume_embedding,
                id_card_image,
                degree_image,
                diploma_image,
                license_image,
                created_at,
                updated_at
            )
            VALUES (
                %(id)s,
                %(name)s,
                %(id_card)s,
                %(license_no)s,
                %(resume)s,
                %(resume_embedding)s,
                %(id_card_image)s,
                %(degree_image)s,
                %(diploma_image)s,
                %(license_image)s,
                %(created_at)s,
                %(updated_at)s
            )
            """,
            payload,
        )

    result = {**payload, "resume_embedding": embedding_list}
    if json_output:
        typer.echo(json.dumps({"status": "ok", **result}, default=str))
    else:
        typer.echo("Lawyer inserted")
# endregion
# ============================================


# ============================================
# region get_lawyer
# ============================================
@app.command("get")
def get_lawyer(
    ctx: typer.Context,
    record_id: int = typer.Option(..., "--id", help="主键ID"),
    json_output: bool = typer.Option(True, "--json", help="输出 JSON"),
) -> None:
    """
    查询律师信息

    参数:
        ctx: Typer 上下文
        record_id: 主键ID
        confirm: 是否跳过确认
        json_output: 是否输出 JSON
    返回:
        None
    """

    with get_connection(_get_db_url(ctx)) as conn:
        row = conn.execute(
            """
            SELECT id, name, id_card, license_no, resume, resume_embedding, id_card_image,
                   degree_image, diploma_image, license_image, created_at, updated_at
            FROM lawyers
            WHERE id = %s
            """,
            (record_id,),
        ).fetchone()

    if not row:
        raise typer.Exit(code=1)

    result = {
        "id": row[0],
        "name": row[1],
        "id_card": row[2],
        "license_no": row[3],
        "resume": row[4],
        "resume_embedding": _normalize_vector(row[5]),
        "id_card_image": row[6],
        "degree_image": row[7],
        "diploma_image": row[8],
        "license_image": row[9],
        "created_at": row[10],
        "updated_at": row[11],
    }

    if json_output:
        typer.echo(json.dumps(result, default=str))
    else:
        typer.echo(f"Lawyer: {result['name']}")
# endregion
# ============================================


# ============================================
# region delete_lawyer
# ============================================
@app.command("delete")
def delete_lawyer(
    ctx: typer.Context,
    record_id: int = typer.Option(..., "--id", help="主键ID"),
    confirm: bool = typer.Option(False, "--yes", help="跳过确认"),
    json_output: bool = typer.Option(False, "--json", help="输出 JSON"),
) -> None:
    """
    删除律师信息

    参数:
        ctx: Typer 上下文
        record_id: 主键ID
        json_output: 是否输出 JSON
    返回:
        None
    """

    if not confirm:
        confirmed = typer.confirm("确认删除律师？")
        if not confirmed:
            raise typer.Exit(code=1)

    with get_connection(_get_db_url(ctx)) as conn:
        row = conn.execute(
            """
            DELETE FROM lawyers
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
        typer.echo("Lawyer deleted")
# endregion
# ============================================
