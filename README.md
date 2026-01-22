# 通用 RAG 知识库（后端 + 终端对话）

本仓库用于构建通用性 RAG 知识库，包含文档解析、向量索引、RAG 问答、业绩管理与 Agent Loop 相关能力。

### 🔥 最新特性 (Agentic RAG)
- **ReAct Agent**: 自主规划 `Think-Act-Observe` 循环，支持复杂问题的多步推理中。
- **智能工具链**: 
  - `MatchTenderTool`: 自动匹配招标需求与业绩。
  - `RAGSearchTool`: 向量检索知识库。
- **安全可靠**: 内置防死循环与速率限制机制。
- **实时反馈**: 支持 SSE 实时推送 Agent 思考与执行状态。

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
- 复制或编辑 `.env`（参考 `.env.example`）
- 至少填写 `DATABASE_URL`

3) 初始化数据库
```bash
psql "${DATABASE_URL}" -f sql/schema_init.sql
```

如需文档结构化入库，再执行：
```bash
psql "${DATABASE_URL}" -f sql/schema_documents.sql
```

4) 启动 FastAPI
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

## CLI 使用（Typer）

```bash
python -m cli.main --db-url ${DATABASE_URL} enterprise insert \
  --credit-code 91320101MA1XXXXXXX \
  --company-name "xx市xx研究院有限公司" \
  --json
```

查看会话列表
```bash
python -m cli.main chat --list
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
- 文档表结构：`sql/schema_documents.sql`
- 索引策略：`sql/schema_indexes.sql`
- 会话表结构：`sql/schema_chat.sql`
- API 示例：`docs/examples_api.md`
- CLI 草案：`docs/cli_typer.md`
- 批量导入模板：`samples/enterprises.json`、`samples/performances.json`、`samples/lawyers.json`

## 单元测试
```bash
python -m unittest discover -s tests
```

## 对话与 SSE（规划）
- 创建会话：POST /chat/sessions
- 会话列表：GET /chat/sessions?limit=10
- 发送消息（SSE）：POST /chat/sessions/{session_id}/messages
- 会话历史：GET /chat/sessions/{session_id}/history
- 历史截断：先取 20 条，再按 2000 字符阈值截断
- 引用入库字段：document_id / filename / chunk_index / preview / score / path

## 环境变量
- `DATABASE_URL`: PostgreSQL 连接串
- `FASTAPI_HOST`: FastAPI 监听地址
- `FASTAPI_PORT`: FastAPI 端口
- `MODEL_API_BASE_URL`: 模型 API 地址
- `MODEL_API_KEY`: 模型 API 密钥
- `LOG_LEVEL`: 日志级别

## 密钥管理
- 不要提交真实密钥，使用 `.env` 本地注入
- 生产环境通过密钥管理系统注入
- 日志与错误信息中禁止输出密钥

## 注意事项
- `.env` 中不要提交真实密钥（当前为占位）
- 依赖已包含 `markitdown` 与 `sse-starlette`，如需锁版本请另行维护
