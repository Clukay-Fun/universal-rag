# universal-rag

通用 RAG 智能体平台 - 支持多智能体动态接入各自数据源

## 快速开始

```bash
# 0. clone repo
git clone https://github.com/Clukay-Fun/universal-rag.git
cd universal-rag

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置 DATABASE_URL 等

# 3. 初始化数据库
psql -U postgres -d your_db -f sql/schema.sql

# 4. 启动服务
python -m api.main
# 服务地址: http://localhost:8001
```

---

## 核心概念

| 概念 | 说明 |
|------|------|
| **Agent (智能体)** | 独立的问答助手，拥有专属 system_prompt 和配置 |
| **Datasource (数据源)** | 智能体可连接的外部数据库 (PostgreSQL/MySQL/API) |
| **Document (文档)** | RAG 知识库中的文档 |
| **Chat Session (会话)** | 用户与智能体的对话记录 |

---

## API 参考

### 智能体管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/agents` | 创建智能体 |
| `GET` | `/agents` | 列出所有智能体 |
| `GET` | `/agents/{agent_id}` | 获取智能体详情 |
| `PUT` | `/agents/{agent_id}` | 更新智能体 |
| `DELETE` | `/agents/{agent_id}` | 删除智能体 |

**创建智能体示例：**
```json
POST /agents
{
  "name": "法律顾问",
  "description": "专业法律咨询智能体",
  "system_prompt": "你是一位专业的法律顾问...",
  "config": {}
}
```

---

### 数据源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/agents/{agent_id}/datasources` | 添加数据源 |
| `GET` | `/agents/{agent_id}/datasources` | 列出数据源 |
| `DELETE` | `/agents/datasources/{datasource_id}` | 删除数据源 |
| `POST` | `/agents/datasources/{datasource_id}/test` | 测试连接 |
| `GET` | `/agents/datasources/{datasource_id}/tables` | 列出表 |
| `POST` | `/agents/datasources/{datasource_id}/query` | 执行查询 |

**添加 PostgreSQL 数据源：**
```json
POST /agents/{agent_id}/datasources
{
  "name": "业务数据库",
  "ds_type": "postgresql",
  "connection_config": {
    "host": "localhost",
    "port": 5432,
    "database": "business_db",
    "user": "postgres",
    "password": "xxx"
  }
}
```

---

### 文档管理 (RAG 知识库)

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/documents/upload` | 上传文档 |
| `GET` | `/documents` | 列出文档 |
| `DELETE` | `/documents/{doc_id}` | 删除文档 |

---

### 向量检索

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/vector/search` | 向量相似度检索 |
| `POST` | `/rag/query` | RAG 问答 (带引用) |

**RAG 查询示例：**
```json
POST /rag/query
{
  "query": "合同违约的法律后果是什么？",
  "top_k": 5
}
```

---

### 对话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/chat/sessions` | 创建会话 |
| `POST` | `/chat/sessions/{session_id}/messages` | 发送消息 (SSE) |
| `GET` | `/chat/sessions/{session_id}/history` | 获取历史 |

---

## 数据库表结构

```
agents                 # 智能体配置
├── agent_id (PK)
├── name, description
├── system_prompt      # 专属提示词
└── config (JSONB)

agent_datasources      # 外接数据源
├── datasource_id (PK)
├── agent_id (FK)
├── ds_type            # postgresql/mysql/api
└── connection_config

documents              # 知识库文档
├── doc_id (PK)
├── agent_id (FK)      # 归属智能体
└── metadata (JSONB)

document_nodes         # 文档分块 + 向量
├── node_id (PK)
├── content, embedding
└── path[]             # 章节路径

chat_sessions          # 对话会话
└── chat_messages      # 消息记录
```

---

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql://user:pass@localhost/db` |
| `FASTAPI_PORT` | 服务端口 | `8001` |
| `MODEL_API_BASE_URL` | LLM API 地址 | `https://api.siliconflow.cn/v1` |
| `MODEL_API_KEY` | API 密钥 | `sk-xxx` |

---

## 目录结构

```
universal-rag/
├── api/              # FastAPI 路由层
│   ├── main.py
│   └── routes/
├── services/         # 业务逻辑层
│   ├── agent_service.py      # Agent Loop 核心
│   ├── agent_management_service.py  # 智能体 CRUD
│   ├── datasource_service.py # 动态数据源
│   └── tools/                # 工具注册
├── db/               # 数据库连接
├── sql/              # Schema 和迁移
├── prompts/          # 提示词模板
└── cli/              # 命令行工具
```

---

## 默认智能体

系统自带一个默认智能体 (ID: `00000000-0000-0000-0000-000000000001`)，不可删除。

---

## 扩展开发

### 添加新工具

```python
# services/tools/my_tool.py
from services.tool_registry import BaseTool, ToolRegistry

@ToolRegistry.register
class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "工具描述"
    param1: str  # 参数定义
    
    def run(self) -> str:
        # 工具逻辑
        return "结果"
```

### 创建专用智能体项目

1. 复制 universal-rag 作为基础
2. 通过 API 创建专用智能体
3. 配置专属数据源
4. 自定义 system_prompt

---

## License

MIT
