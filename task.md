# 开发清单

## 基础与规范
- [x] 创建数据库 `universal-rag`
- [x] 生成初始化与迁移 SQL 文档
- [x] 建立索引策略（查询常用字段）
- [x] 补充环境变量清单与密钥管理规范

## 文档解析与结构化
- [x] Word → MarkItDown 转换
- [x] 章节层级解析与 Node 树生成
- [x] 结构化结果入库
- [x] 节点路径注入（Path/Lineage）

## 向量化与检索
- [x] BGE-M3 向量化任务
- [x] 向量入库与 ivfflat 索引
- [x] pgvector 相似度检索接口
- [x] 模型调用配置接入

## RAG 问答
- [x] 检索增强生成链路
- [x] 引用格式规范输出（document_id/node_id/score）
- [x] 引用展示优化（filename/preview/score）

## SSE 实时状态
### 基础架构
- [x] SSE 事件工具类 `services/sse_utils.py`（标准化事件格式）
- [x] 状态枚举定义（THINKING / EXECUTING / DONE / ERROR）

## Agent Loop 与工具系统
### 基础设施
- [x] 工具注册表 `services/tool_registry.py` (BaseTool, Registry)
- [x] 通用工具集 `services/tools/` (RAGTool)

### Agent Core
- [x] Agent 执行循环 `services/agent_service.py` (Think-Act-Observe)
- [x] 系统提示词模板 `prompts/agent/system.md` (定义工具协议)
- [x] 状态机与错误处理 (Max Steps, Error Recovery)

### 集成与测试
- [x] 集成到 `api/routes/chat.py` (替换原 RAG 逻辑)
- [ ] 单元测试与集成测试

## 对话与会话（SSE）
- [x] chat_sessions/chat_messages 表
- [x] SSE 会话消息接口（POST /chat/sessions/{id}/messages）
- [x] 会话历史截断（20 条 + 2000 字符）
- [x] 引用写入会话消息（document_id/node_id/score/path）
- [x] 会话列表接口（GET /chat/sessions?limit=10）
- [x] CLI chat 交互模式

## FastAPI
- [x] 文档结构化检索与节点搜索 API

## CLI 与运维
- [x] Typer CLI 骨架
- [x] CLI chat --list 会话列表
- [x] CLI 读取 .env 覆盖环境变量
