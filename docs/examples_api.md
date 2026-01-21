# API 请求/响应示例（JSON）

## 文档解析

POST /documents/parse

响应示例
```json
{
  "doc_id": 12,
  "title": "示例合同",
  "file_name": "sample.docx",
  "nodes": [
    {
      "node_id": 1,
      "parent_id": null,
      "level": 1,
      "title": "第一章 总则",
      "content": "..."
    }
  ],
  "stats": {
    "node_count": 12,
    "chunk_count": 38
  }
}
```

## 向量化入库

POST /embeddings/build

请求示例
```json
{
  "doc_id": 12,
  "chunk_strategy": "heading",
  "batch_size": 64
}
```

响应示例
```json
{
  "doc_id": 12,
  "chunks_stored": 38,
  "status": "ok"
}
```

## 向量检索

POST /search/vector

请求示例
```json
{
  "query_text": "合同金额与签订日期",
  "top_k": 5,
  "filters": {
    "doc_id": 12
  }
}
```

响应示例
```json
{
  "query_text": "合同金额与签订日期",
  "hits": [
    {
      "chunk_id": 1201,
      "source_id": "doc-12",
      "score": 0.8123
    }
  ]
}
```

## RAG 问答（带引用）

POST /qa/ask

请求示例
```json
{
  "question": "本合同的金额是多少？",
  "top_k": 4,
  "filters": {
    "doc_id": 12
  }
}
```

响应示例
```json
{
  "answer": "合同金额为 5 万元。",
  "citations": [
    {
      "source_id": "doc-12",
      "chunk_id": 1201,
      "paragraph_index": 3,
      "score": 0.8123,
      "source_title": "示例合同"
    }
  ]
}
```

## 合同信息提取

POST /contracts/extract

响应示例
```json
{
  "contract_name": "法律顾问服务合同",
  "party_a": "xx市xx研究院有限公司",
  "party_a_id": "91320101MA1XXXXXXX",
  "party_a_industry": "社会经济咨询",
  "is_state_owned": true,
  "is_individual": false,
  "amount": 5,
  "fee_method": "按年支付，合同签订后30日内支付。",
  "sign_date_raw": "2024年01月15日",
  "sign_date_norm": "2024-01-15",
  "project_type": "常年法律顾问",
  "project_detail": "(1)就各种经营活动中出现的问题提供法律咨询...",
  "subject_amount": null,
  "opponent": null,
  "team_member": "张三,李四",
  "summary": null
}
```

## 合同入库

POST /contracts/store

请求示例
```json
{
  "source_id": "contract-2024-001",
  "file_name": "contract-001.png",
  "image_ref": "s3://bucket/contracts/contract-001.png",
  "prompt_id": "contract_extract",
  "prompt_version": "v1",
  "data": {
    "contract_name": "法律顾问服务合同",
    "party_a": "xx市xx研究院有限公司",
    "party_a_id": "91320101MA1XXXXXXX",
    "party_a_industry": "社会经济咨询",
    "is_state_owned": true,
    "is_individual": false,
    "amount": 5,
    "fee_method": "按年支付，合同签订后30日内支付。",
    "sign_date_raw": "2024年01月15日",
    "sign_date_norm": "2024-01-15",
    "project_type": "常年法律顾问",
    "project_detail": "(1)就各种经营活动中出现的问题提供法律咨询...",
    "subject_amount": null,
    "opponent": null,
    "team_member": "张三,李四",
    "summary": null
  }
}
```

响应示例
```json
{
  "contract_id": 1001,
  "status": "stored"
}
```

## 智能匹配

POST /matches/run

请求示例
```json
{
  "tender_id": 3001,
  "top_k": 5
}
```

响应示例
```json
{
  "tender_id": 3001,
  "matches": [
    {
      "contract_id": 1001,
      "score": 0.9234,
      "reasons": [
        "项目类型匹配: 常年法律顾问",
        "行业匹配: 社会经济咨询"
      ]
    }
  ]
}
```

## 企业删除

DELETE /enterprises/{credit_code}

响应示例
```json
{
  "credit_code": "91320101TEST00001",
  "deleted": true
}
```

## 业绩删除

DELETE /performances/{record_id}

响应示例
```json
{
  "id": 1001,
  "deleted": true
}
```

## 律师删除

DELETE /lawyers/{record_id}

响应示例
```json
{
  "id": 501,
  "deleted": true
}
```

## 文档结构化结果

GET /documents/{doc_id}/structure

响应示例
```json
{
  "doc_id": 1,
  "model_name": "Qwen/Qwen3-8B",
  "payload": {
    "title": "文档标题",
    "level": 0,
    "content": "",
    "children": []
  },
  "raw_text": "{...}",
  "error": null,
  "created_at": "2026-01-20T14:48:02.817982"
}
```

## 文档节点树

GET /documents/{doc_id}/tree

响应示例
```json
{
  "title": "文档标题",
  "level": 0,
  "content": "",
  "children": [],
  "path": ["文档标题"]
}
```

## 文档节点搜索

GET /documents/nodes/search?query=法律顾问&title=第三条&path=常年法律顾问合同

响应示例
```json
[
  {
    "doc_id": 1,
    "node_id": 23,
    "title": "第三条 法律顾问工作范围",
    "content": "...",
    "path": ["常年法律顾问合同", "第三条 法律顾问工作范围"],
    "party_a_name": "深圳市深汕特别合作区深燃天然气有限有限公司",
    "party_a_credit_code": null,
    "score": 0.42
  }
]
```

## 文档向量化

POST /vectors/document-nodes

请求示例
```json
{
  "doc_id": 1,
  "batch_size": 16
}
```

响应示例
```json
{
  "doc_id": 1,
  "processed": 10,
  "updated": 10
}
```

## 向量检索

POST /vectors/search

请求示例
```json
{
  "query_text": "法律顾问费用",
  "top_k": 5,
  "doc_id": 1
}
```

响应示例
```json
{
  "query_text": "法律顾问费用",
  "hits": [
    {
      "doc_id": 1,
      "node_id": 23,
      "title": "第八条 法律顾问费用及其支付",
      "content": "...",
      "path": ["常年法律顾问合同", "第八条 法律顾问费用及其支付"],
      "party_a_name": "深圳市深汕特别合作区深燃天然气有限有限公司",
      "party_a_credit_code": null,
      "score": 0.12
    }
  ]
}
```
