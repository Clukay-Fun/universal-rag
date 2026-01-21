请从合同文本中提取以下字段，并输出 JSON（不要包含代码块）：

{
  "contract_name": "...",
  "party_a": "...",
  "party_a_id": "...",
  "party_a_industry": "...",
  "is_state_owned": false,
  "is_individual": false,
  "amount": 0,
  "fee_method": "...",
  "sign_date": "YYYY-MM-DD",
  "project_type": "常法/诉讼/专项",
  "project_detail": "...",
  "subject_amount": null,
  "opponent": null,
  "team_member": "...",
  "summary": null
}

规则:
- amount 单位为万元，必要时换算。
- sign_date 保持原文格式即可。
- project_type 使用文中真实类型，可扩展。
- team_member 保留姓名，使用逗号分隔。
- 无法识别字段可为空字符串或 null。
