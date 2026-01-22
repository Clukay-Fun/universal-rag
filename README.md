# Universal RAG

基于 Agentic RAG 架构的通用检索增强生成系统。集成了向量检索、智能业绩匹配、Agent 工具调用循环以及实时流式响应（SSE）。

## ✨ 核心特性

- **Agentic RAG**: 采用 ReAct 范式（Think-Act-Observe），Agent 可自主决策调用搜索工具或匹配工具。
- **智能匹配 (Intelligent Matching)**: 基于招标需求自动匹配最合适的合同业绩，支持多维度筛选（金额、日期、项目类型）。
- **向量检索 (Vector Search)**: 使用 `BGE-M3` 模型生成嵌入，基于 `pgvector` 实现高效语义检索。
- **实时流式响应 (SSE)**: 支持 Server-Sent Events，实时推送 Agent 思考过程、工具调用状态和最终结果。
- **统一数据架构**: 简化的数据库 Schema，统一管理业绩（Performances）、文档（Documents）和向量数据。

## 🛠️ 技术栈

- **Backend**: Python 3.10+, FastAPI
- **Database**: PostgreSQL 15+ (with `pgvector` extension)
- **LLM Integration**: OpenAI Compatibility Interface (DeepSeek / SiliconFlow / etc.)
- **CLI**: Typer
- **Vector Model**: BAAI/bge-m3

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.10+ 和 PostgreSQL 15+（需启用 pgvector）。

```bash
# 克隆项目
git clone <repo_url>
cd universal-rag

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例配置并填写密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```ini
DATABASE_URL=postgresql://user:pass@localhost:5432/universal-rag
MODEL_API_KEY=your_api_key
MODEL_API_BASE_URL=https://api.siliconflow.cn/v1  # 或其他兼容接口
EMBEDDING_MODEL=BAAI/bge-m3
```

### 3. 数据库初始化

使用统一的 Schema 初始化数据库：

```bash
# 确保数据库已创建
createdb universal-rag

# 导入表结构
psql "${DATABASE_URL}" -f sql/schema.sql
```

### 4. 启动服务

```bash
# 启动 API 服务 (默认端口 8001)
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

## 💻 CLI 使用指南

项目提供了强大的命令行工具，支持所有核心功能。

### 🤖 Agent 对话

启动交互式 Agent 对话，支持工具调用：

```bash
python -m cli.main chat
```

- 输入问题，例如："帮我找一下最近金额大于100万的软件开发业绩"
- Agent 会自动拆解任务，调用 `match_tender` 或 `search_knowledge_base` 工具。

### 📑 业绩管理

```bash
# 导入业绩数据
python -m cli.main performance import --file samples/performances.json

# 查询业绩
python -m cli.main performance list --limit 5
```

### 🔍 智能匹配

```bash
# 实时流式匹配 (Stream Mode)
python -m cli.main matching match --tender-id 1 --top-k 3 --stream
```

## 📂 目录结构

```
universal-rag/
├── api/                # FastAPI 路由与应用入口
├── cli/                # Typer 命令行工具
├── db/                 # 数据库连接与会话管理
├── services/           # 核心业务逻辑
│   ├── agent_service.py    # Agent 循环与状态机
│   ├── tool_registry.py    # 工具注册中心
│   ├── tools/              # 具体工具实现 (MatchTool, RAGTool)
│   ├── matching_service.py # 智能匹配逻辑
│   └── vector_service.py   # 向量检索服务
├── sql/                # 数据库 SQL 脚本
│   ├── schema.sql          # 完整数据库结构
│   └── migrations/         # 迁移脚本
├── prompts/            # LLM 提示词模板
├── schemas/            # Pydantic 数据模型
└── tests/              # 单元测试
```
