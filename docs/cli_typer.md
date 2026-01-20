# Typer CLI 目录与命令草案

## 目录结构建议
```
cli/
  main.py
  commands/
    parse_doc.py
    index_build.py
    search_vector.py
    qa_ask.py
    contract_extract.py
    contract_store.py
    match_run.py
    agent_run.py
    agent_stream.py
```

## 入口说明
- `cli/main.py` 作为 Typer 入口，注册所有子命令
- 统一命令风格：短横线命名（如 parse-doc）
- 输出模式：默认摘要，`--json` 输出完整结构

## 命令草案

### 解析文档
```
python -m cli.main parse-doc --file path/to/doc.docx --out output.json
```

参数
- `--file` 文档路径
- `--out` 输出路径
- `--json` 输出完整 JSON

### 向量入库
```
python -m cli.main index-build --doc-id 12 --batch-size 64
```

参数
- `--doc-id` 文档 ID
- `--batch-size` 批量大小

### 向量检索
```
python -m cli.main search --query "合同金额" --top-k 5
```

参数
- `--query` 查询文本
- `--top-k` 返回数量
- `--filter` 过滤条件（JSON 字符串）

### RAG 问答
```
python -m cli.main qa --question "合同金额是多少" --top-k 4 --show-citations
```

参数
- `--question` 问题文本
- `--top-k` 召回数量
- `--show-citations` 显示引用

### 合同信息提取
```
python -m cli.main contract-extract --file contract.png --out contract.json
```

参数
- `--file` 合同图片或扫描件
- `--out` 输出路径
- `--json` 输出完整 JSON

### 合同入库
```
python -m cli.main contract-store --file contract.png --data contract.json
```

参数
- `--file` 原始文件路径
- `--data` 结构化 JSON 路径

### 智能匹配
```
python -m cli.main match-run --req-file tender.txt --top-k 5
```

参数
- `--req-file` 招标需求文本
- `--top-k` 返回数量

### 企业/业绩/律师
```
python -m cli.main enterprise insert --credit-code CODE --company-name NAME
python -m cli.main enterprise get --credit-code CODE
python -m cli.main enterprise delete --credit-code CODE --yes
python -m cli.main enterprise import --file samples/enterprises.json
python -m cli.main enterprise export --out enterprises_export.json

python -m cli.main performance insert --id 1001 --amount 5
python -m cli.main performance get --id 1001
python -m cli.main performance delete --id 1001 --yes
python -m cli.main performance import --file samples/performances.json
python -m cli.main performance export --out performances_export.json

python -m cli.main lawyer insert --id 1 --name "张三"
python -m cli.main lawyer get --id 1
python -m cli.main lawyer delete --id 1 --yes
python -m cli.main lawyer import --file samples/lawyers.json
python -m cli.main lawyer export --out lawyers_export.json
```

### Agent 运行
```
python -m cli.main agent-run --task "解析文档并问答" --max-steps 10 --timeout 120
```

参数
- `--task` 任务描述
- `--max-steps` 最大步数
- `--timeout` 超时时间（秒）

### SSE 实时状态
```
python -m cli.main agent-stream --task "执行问答" --stream
```

参数
- `--task` 任务描述
- `--stream` 开启 SSE 模式
