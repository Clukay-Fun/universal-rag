# Typer CLI 插入/查询示例

## 企业信息

插入
```
python -m cli.main --db-url postgresql://postgres:1234@localhost:5432/universal-rag \
  enterprise insert \
  --credit-code 91320101MA1XXXXXXX \
  --company-name "xx市xx研究院有限公司" \
  --business-scope "社会经济咨询" \
  --industry "社会经济咨询" \
  --enterprise-type "国企" \
  --json
```

查询
```
python -m cli.main --db-url postgresql://postgres:1234@localhost:5432/universal-rag \
  enterprise get \
  --credit-code 91320101MA1XXXXXXX \
  --json
```

## 业绩/合同

插入
```
python -m cli.main --db-url postgresql://postgres:1234@localhost:5432/universal-rag \
  performance insert \
  --id 1001 \
  --file-name contract-001.png \
  --party-a "xx市xx研究院有限公司" \
  --party-a-id 91320101MA1XXXXXXX \
  --contract-number 1 \
  --amount 5 \
  --fee-method "按年支付，合同签订后30日内支付。" \
  --sign-date-raw "2024年01月15日" \
  --project-type "常年法律顾问" \
  --project-detail "(1)就各种经营活动中出现的问题提供法律咨询..." \
  --team-member "张三,李四" \
  --json
```

查询
```
python -m cli.main --db-url postgresql://postgres:1234@localhost:5432/universal-rag \
  performance get \
  --id 1001 \
  --json
```
