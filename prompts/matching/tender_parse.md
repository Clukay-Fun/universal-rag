# 招标需求解析提示词

请从以下招标/投标文本中提取业绩筛选约束条件，输出 JSON（不要包含代码块）：

{
  "title": "招标项目名称",
  "project_types": ["常法", "诉讼", "专项"],
  "industries": ["房地产", "金融", "制造业"],
  "min_amount": 10,
  "max_amount": null,
  "min_subject_amount": null,
  "max_subject_amount": null,
  "date_after": "2020-01-01",
  "date_before": null,
  "require_state_owned": null,
  "min_count": 3,
  "keywords": ["合同纠纷", "股权争议"],
  "other_requirements": "其他特殊要求原文"
}

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 招标项目名称，从原文提取 |
| project_types | string[] | 要求的项目类型列表，如常法、诉讼、专项、非诉等 |
| industries | string[] | 要求的行业领域，如房地产、金融、制造业等 |
| min_amount | number | 最低合同金额（万元），无要求填 null |
| max_amount | number | 最高合同金额（万元），无要求填 null |
| min_subject_amount | number | 最低标的金额（万元），无要求填 null |
| max_subject_amount | number | 最高标的金额（万元），无要求填 null |
| date_after | string | 业绩起始日期（YYYY-MM-DD），如"近三年"则计算具体日期 |
| date_before | string | 业绩截止日期（YYYY-MM-DD），无要求填 null |
| require_state_owned | boolean | 是否要求国有企业业绩，无要求填 null |
| min_count | number | 要求的最少业绩数量，无要求填 null |
| keywords | string[] | 关键词列表，用于模糊匹配项目详情 |
| other_requirements | string | 其他无法结构化的特殊要求原文 |

## 规则

1. 金额单位统一转换为万元
2. "近三年"等相对时间需转换为具体日期（基于当前日期）
3. 无法识别或未提及的字段填 null 或空数组
4. project_types 和 industries 尽量使用标准化术语
5. 如有数量要求（如"不少于3个"），提取到 min_count

## 招标原文

