---
name: copy-legend-config
description: 为 cfg_gis_kpi 和 cfg_gis_kpi_color 生成 Greenplum 兼容的 GIS 图例配置复制 SQL。适用于用户要从源模块（如统一GIS）复制指标图例/颜色配置到目标模块、提供 KPI 中文名或字段名、需要 AI 智能匹配未命中指标，或只想生成可审查 SQL 而不执行 SQL 的场景。
---

# 图例配置复制

## 概览

使用此 skill 将用户提供的 KPI 列表、源模块和目标模块转换成可审查的 SQL，用于插入 GIS KPI 图例配置。它也支持把现有模块的 `cfg_gis_kpi` 和 `cfg_gis_kpi_color` 配置导出为 CSV。

默认生成 Greenplum 兼容 SQL。确定性的数据库查询、匹配候选生成、SQL 生成和 CSV 导出交给脚本完成；AI 只处理未匹配或语义模糊的候选选择。

## 必要输入

生成复制 SQL 前收集：

- 数据库连接来源：输入 JSON 的 `database`、`LEGEND_DB_*` 环境变量、`LEGEND_DB_CONFIG` 指向的 JSON，或 skill 根目录下的私有 `local.database.json`。
- 源范围：`business_name`，以及已知时的 `net_type`、`kpi_dim`。
- 目标模块：新的 `business_name`。
- KPI 列表：每项应包含 `kpi_name_cn`；如果目标数据库字段名已知，包含 `kpi_name`。
- 可选覆盖：`kpi_type`/`kpiType`、`order_num`，或手工指定源指标中文名的 `search`。

不要把数据库密码写入生成 SQL、SQL 注释或用户可见总结。

## 复制 SQL 流程

1. 需要表字段、匹配规则或 AI 候选选择规则时，读取 `references/legend-config.md`。
2. 需要调整语义族、归一化停用词或打分阈值时，编辑或指定 `references/matching-rules.json`。
3. 将用户 KPI 列表整理成 `scripts/prepare_legend_copy.py` 接受的 JSON。
4. 只用数据库做只读源配置查询；绝不执行生成的 insert SQL。
5. 按以下顺序匹配 KPI：
   - 使用用户提供的 `search` 精确匹配。
   - 在源范围内精确匹配 `kpi_name_cn`。
   - 去除单位、括号、空格和常见前后缀后做归一化匹配。
   - 从源模块全部指标中按关键词、KPI 类型和名称相似度生成语义候选。
   - 由 AI 从候选中选择最合理来源；不得使用固定兜底模板。
   - 无法可靠匹配时保留为 SQL 注释。
6. 已确定来源后再生成 SQL。
7. SQL 注释必须标明源 KPI 名称和源 `kpi_id`；AI 语义匹配必须写简短原因。
8. 目标 `kpi_type` 优先使用用户提供的 `kpi_type`/`kpiType`，只有未提供时才复制源值。
9. 目标行固定生成 `login_id = NULL`、`visable = 1`、`colored = 1`。
10. 返回 SQL 文件路径，并说明已匹配、AI 决策和未解析数量。

## CSV 导出流程

1. 字段范围或表规则不确定时，读取 `references/legend-config.md`。
2. 使用 `scripts/export_legend_csv.py` 导出模块配置；不得添加写语句。
3. 按 `business_name` 过滤 `cfg_gis_kpi`，并在用户提供时继续按 `net_type`、`kpi_dim` 缩小范围。
4. 只导出已返回 KPI 的 `cfg_gis_kpi_color` 行。
5. 两张表分别写入 CSV，并使用 UTF-8 BOM，方便 Windows 工具打开。
6. 返回两个输出文件路径和导出行数。

## 辅助脚本

复制 SQL 使用 `scripts/prepare_legend_copy.py`。

输入 JSON 示例：

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

常用命令：

```bash
python scripts/prepare_legend_copy.py --input request.json --analysis match-analysis.json
python scripts/prepare_legend_copy.py --input request.json --decisions match-analysis.json --output legend-copy.sql
python scripts/prepare_legend_copy.py --input request.json --matching-rules references/matching-rules.json --analysis match-analysis.json
```

当脚本输出 `needs_ai_decision` 时，检查候选列表并选择最合理的 `source_kpi_id`。低置信度时保持未解析，让 SQL 输出注释而不是插入语句。

CSV 导出使用 `scripts/export_legend_csv.py`。

```bash
python scripts/export_legend_csv.py --business-name "统一GIS-V2" --output-dir ./exports
python scripts/export_legend_csv.py --input export-request.json --output-dir ./exports
```

导出输入 JSON 示例：

```json
{
  "filter": {
    "business_name": "统一GIS-V2",
    "net_type": "4G",
    "kpi_dim": "小区"
  }
}
```

## 安全规则

- 只生成 SQL 文件，不执行生成的 SQL。
- 源配置查询只能使用 `SELECT`。
- CSV 导出只能使用 `SELECT`，不得执行 update、delete、insert 或 DDL。
- 默认生成 Greenplum 兼容 SQL，不使用可写 CTE、`INSERT ... RETURNING` 或包含数据修改语句的 `WITH`。
- 优先使用独立语句：先插入 `cfg_gis_kpi`，再根据目标业务字段解析目标 `kpi_id` 并插入 `cfg_gis_kpi_color`。
- 尽量保持幂等：KPI 行用目标业务字段 `WHERE NOT EXISTS` 防重复；颜色行按目标 KPI 实际 `kpi_id` 和颜色区间字段防重复。
- 保留用户提供的目标字段。特别是 `kpi_type`/`kpiType` 必须覆盖源 `kpi_type`。
- 不要臆造目标 `kpi_name`；缺失时询问用户或保留未解析注释。
- 除非用户明确要求，或同范围没有合理候选且 SQL 注释说明原因，否则不要跨 `net_type` 或 `kpi_dim` 复制。
- 模糊匹配作为复核项处理，不要强行插入。
