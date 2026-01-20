# 通用 RAG 知识库（后端 + 终端对话）

本仓库用于构建通用性 RAG 知识库，包含文档解析、向量索引、RAG 问答、业绩管理与 Agent Loop 相关能力。

## 快速开始

1) 创建虚拟环境并安装依赖
```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

2) 配置环境变量
- 复制或编辑 `.env`
- 至少填写 `DATABASE_URL`

3) 初始化数据库
```bash
psql "${DATABASE_URL}" -f sql/schema_init.sql
```

## CLI 使用（Typer）

```bash
python -m cli.main --db-url ${DATABASE_URL} enterprise insert \
  --credit-code 91320101MA1XXXXXXX \
  --company-name "xx市xx研究院有限公司" \
  --json
```

完整示例见 `docs/cli_examples.md`。

## 目录结构

```
cli/                 Typer CLI
docs/                设计与示例文档
sql/                 初始化与迁移脚本
task.md              开发清单
AGENTS.md            Agent 协作规范
```

## 文档与脚本
- SQL 初始化与约束：`sql/schema_init.sql`、`sql/schema_constraints.sql`
- 迁移记录：`sql/schema_migration.sql`
- API 示例：`docs/examples_api.md`
- CLI 草案：`docs/cli_typer.md`

## 注意事项
- `.env` 中不要提交真实密钥（当前为占位）
- `requirements.txt` 中部分依赖包名需根据实际确认
