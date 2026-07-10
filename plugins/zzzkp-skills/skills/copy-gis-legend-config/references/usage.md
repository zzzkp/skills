# 使用说明

## 复制请求

```json
{
  "source_filter": {
    "business_name": "统一GIS",
    "net_type": "4G",
    "kpi_dim": "小区"
  },
  "target": {
    "business_name": "新模块"
  },
  "kpis": [
    {
      "kpi_name": "target_field",
      "kpi_name_cn": "下行PRB平均利用率"
    }
  ]
}
```

```bash
python scripts/prepare_legend_copy.py --input request.json --analysis match-analysis.json
python scripts/prepare_legend_copy.py --input request.json --decisions match-analysis.json --output legend-copy.sql
python scripts/prepare_legend_copy.py --input request.json --matching-rules references/matching-rules.json --analysis match-analysis.json
```

脚本输出 `needs_ai_decision` 时，检查候选列表并选择最合理的 `source_kpi_id`。置信度不足时保持未解析，让 SQL 输出注释。

## CSV 导出

```json
{
  "filter": {
    "business_name": "统一GIS-V2",
    "net_type": "4G",
    "kpi_dim": "小区"
  }
}
```

```bash
python scripts/export_legend_csv.py --business-name "统一GIS-V2" --output-dir ./exports
python scripts/export_legend_csv.py --input export-request.json --output-dir ./exports
```
