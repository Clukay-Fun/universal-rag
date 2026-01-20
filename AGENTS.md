# AGENTS.md
# 通用 RAG 知识库协作指南（中文）

## 项目定位
- 目标：通用性 RAG 知识库（后端 + 终端对话）
- 关键体验：SSE 实时展示 Agent 状态
- 默认服务地址：http://localhost:8001/

## 模块与功能
- 文档解析：Word -> MarkItDown，保留结构
- 知识库：AI 解析章节层级，生成 Node 树
- 向量索引：pgvector 存储，BGE-M3 嵌入
- RAG 问答：引用来源的智能问答
- 业绩管理：合同信息提取（视觉 + 结构化）
- 数据库存储：PostgreSQL 存结构化 + 图片
- 智能匹配：根据招标要求筛选业绩

## 固定依赖（必须使用）
- 文档解析：MarkItDown、python-docx
- 向量化：BAAI/bge-m3（硅基流动 API）
- 重排序：BAAI/bge-reranker-v2-m3
- JSON 提取/标书解析：Qwen3-8B
- 视觉识别：GLM-4.1V-Thinking
- 规划与复杂推理：DeepSeek-R1-0528-Qwen3-8B
- 向量/关系数据库：PostgreSQL + pgvector
- 框架：LlamaIndex
- 对话模型：internlm/internlm2_5-7b-chat
- Web 框架：FastAPI

## 环境变量与密钥管理
- 必填：`DATABASE_URL`（PostgreSQL 连接串）
- 服务：`FASTAPI_HOST`、`FASTAPI_PORT`
- 模型：`MODEL_API_BASE_URL`、`MODEL_API_KEY`
- 日志：`LOG_LEVEL`
- 本地开发使用 `.env`，生产环境使用受控的 Secret 管理系统
- 禁止提交真实密钥；仅保留 `.env.example`
- 避免在日志、错误信息、追踪中输出密钥或敏感字段
- 不同环境使用不同密钥，定期轮换

## 单测运行（占位符模板）
- Pytest：pytest path/to/test.py::TestClass::test_name
- 单文件：pytest path/to/test.py
- 过滤用例：pytest -k "keyword"
- 其他框架：<single-test-command>  # 待补充

## Agent Loop（Think-Execute）
- 支持多轮规划与多轮工具调用
- 状态机：THINKING / EXECUTING / DONE / ERROR
- 必须有限步数控制，防止无限循环
- 必须有超时控制（全局与单步）
- 错误处理：可重试，但需退避与上限
- 任一步失败需输出可追踪的错误上下文

## 工具系统（框架化）
- 工具自动注册，避免硬编码 if-else
- 工具分级：固定工具 / 可选工具
- 新增工具不改核心流程
- 禁用自动执行，手动管理 ToolCalling
- 工具失败：记录原因、输入、重试次数
- 工具结果：必须进入对话历史

## RAG 知识库链路
- Markdown 文档解析与分块
- Embedding 生成并落库
- pgvector 相似度检索（<->）
- ivfflat 索引优化，支持 10 万+ 向量
- 结构化与向量数据同库一致性

## SSE 实时通信
- SSE 推送 Agent 状态变化
- 前端/终端可实时看到执行过程
- 简单可靠的单向推送模型

## 开发约定（强制）
- Python 3.11+；依赖管理：requirements.txt
- 每个 Python 文件首行添加三引号注释
- 目录分层：api/、services/、db/、schemas/
- 类型提示必填；禁止无类型返回
- 避免全局 Session；用依赖注入或上下文管理
- 数据库存储：PostgreSQL + pgvector
- 默认向量维度 1024，余弦相似度
- 不使用 Redis；缓存暂缓

## 格式与导入
- 优先使用项目格式化工具
- 行长度目标 100-120 字符
- 导入分组：标准库 / 第三方 / 本地
- 组内按字母排序，禁止未使用导入

## 命名与类型
- 命名清晰且领域优先
- bool 命名使用谓词形式
- 公开 API 与导出符号必须显式类型
- 避免 any / object 等过宽类型

## 错误处理与日志
- 不吞异常，必须明确处理
- 错误信息包含上下文（输入、阶段、标识）
- 禁止抛出裸字符串
- 日志简洁，避免敏感信息

## 函数与结构
- 单一职责，保持小函数
- 复杂参数使用对象参数
- 采用 guard clause 提前返回
- 注释仅用于非显而易见逻辑

## region 注释规范
```python
# ============================================
# region 区域名称
# ============================================

# 这里是代码...

# endregion
# ============================================
```

## 函数/类注释模板
```python
def function_name(param: str) -> dict:
    """
    函数功能简述

    参数:
        param: 参数说明
    返回:
        返回值说明
    """
    pass
```

## 文件头模板（每个 Python 文件必须）
```python
"""
描述: 简述职责
主要功能:
    - 功能1
    - 功能2
依赖: 关键依赖
"""
```

## 数据库与索引规范
- 使用 PostgreSQL + pgvector 一体化存储
- 结构化数据与向量数据保持事务一致
- 索引：ivfflat；根据数据规模调整 lists
- 查询：使用 <-> 作为相似度排序

## 更新清单（仓库完善后）
- 用真实命令替换 Build/Lint/Test/Format/Dev
- 补充 CI/部署/环境变量规范
- 补充实际目录结构与模块边界
- 更新单测示例为真实路径
- 标注模型版本与调用额度限制
