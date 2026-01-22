# 开发清单

## 基础与规范
- [x] 创建数据库 `universal-rag`
- [x] 初始化三张业务表（enterprises / lawyers / performances）
- [x] 应用主键与校验约束（amount/subject_amount）
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
- [x] 引用格式规范输出（source_id/chunk_id/score）
- [x] 引用展示优化（filename/preview/score）

## 业绩管理
- [x] 合同信息提取提示词管理
- [x] 合同结构化提取
- [x] 业绩入库与查询

## 智能匹配
### 数据库与 Schema
- [x] 创建 `TenderRequirementCreate` / `TenderRequirementResponse` Schema
- [x] 创建 `ContractMatchCreate` / `ContractMatchResponse` Schema
- [ ] 确认 `tender_requirements` / `contract_matches` 表已迁移（database_schema.sql）

### 提示词管理
- [x] 创建招标需求解析提示词 `prompts/matching/tender_parse.md`
- [x] 创建匹配评分提示词 `prompts/matching/match_score.md`

### 服务层
- [x] 实现 `tender_service.py`：招标需求解析（调用模型提取约束条件）
- [x] 实现 `matching_service.py`：匹配逻辑（筛选 + 评分 + 理由生成）
- [x] 支持多维度约束过滤（金额区间、项目类型、行业、时间范围）

### API 路由
- [x] POST `/matching/tenders`：创建招标需求
- [x] GET `/matching/tenders/{tender_id}`：查询招标需求详情
- [x] POST `/matching/tenders/{tender_id}/match`：执行匹配并返回结果
- [x] GET `/matching/tenders/{tender_id}/results`：查询匹配结果列表

### CLI 命令
- [x] `cli/commands/matching.py`：tender insert / query / match 命令

### 测试
- [ ] 单元测试：`tests/test_matching_service.py`

## SSE 实时状态
- [ ] SSE 状态推送与终端展示

## Agent Loop 与工具系统
- [ ] 状态机与最大步数控制
- [ ] 工具注册与失败处理
- [ ] 工具结果写回对话历史

## 对话与会话（SSE）
- [x] chat_sessions/chat_messages 表
- [x] SSE 会话消息接口（POST /chat/sessions/{id}/messages）
- [x] 会话历史截断（20 条 + 2000 字符）
- [x] 引用写入会话消息（source_id/node_id/score/path）
- [x] 会话列表接口（GET /chat/sessions?limit=10）
- [x] CLI chat 交互模式

## FastAPI
- [x] Pydantic Schema（企业/业绩）
- [x] 企业/业绩新增与查询路由
- [x] 律师新增与查询路由
- [x] 律师删除路由
- [x] 企业/业绩删除路由
- [x] 文档结构化检索与节点搜索 API

## CLI 与运维
- [x] Typer CLI 骨架
- [x] 企业插入/查询命令
- [x] 业绩插入/查询命令
- [x] 律师插入/查询命令
- [x] 企业/业绩/律师删除命令
- [x] CLI 增加批量导入与导出
- [x] CLI chat --list 会话列表
- [x] CLI 读取 .env 覆盖环境变量
- [x] 单测与示例脚本
