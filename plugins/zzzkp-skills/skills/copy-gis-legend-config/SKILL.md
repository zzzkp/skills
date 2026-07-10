---
name: copy-gis-legend-config
description: >
  复制、迁移、导入、导出或审查 GIS 图例与指标颜色配置，并生成 Greenplum 兼容的 SQL 或 CSV。
  当任务涉及源模块、目标模块、KPI 列表、cfg_gis_kpi 或 cfg_gis_kpi_color 配置时使用。
---

# GIS 图例配置复制

## 目标

根据源模块配置和目标 KPI 列表生成可审查、尽量幂等的图例配置 SQL，或将现有模块的 KPI 与颜色配置导出为 CSV。使用脚本完成数据库查询、候选生成和文件输出，只让 AI 处理语义模糊的候选选择。

## 必要输入

- 确认数据库连接来自环境变量、用户指定的外部配置文件或输入 JSON；不要在 Skill 目录保存私有凭据。
- 确认源 `business_name`，并在已知时收集 `net_type`、`kpi_dim`。
- 确认目标 `business_name` 和 KPI 列表；每项至少包含 `kpi_name_cn`。
- 保留用户提供的 `kpi_name`、`kpi_type`、`order_num` 和手工匹配条件 `search`。

## 复制工作流

1. 需要核对表字段和匹配规则时，读取 [references/legend-config.md](references/legend-config.md)。
2. 将请求整理为 `scripts/prepare_legend_copy.py` 接受的 JSON。
3. 只使用 `SELECT` 查询源配置，不执行生成的写入 SQL。
4. 依次尝试手工 `search`、中文名精确匹配、归一化匹配和语义候选匹配。
5. 仅在候选信息足够时选择来源 KPI；低置信度项目保持未解析并输出 SQL 注释。
6. 生成 SQL 后报告精确匹配、AI 决策和未解析数量。

## 匹配与生成规则

- 优先使用用户提供的目标字段；目标 `kpi_type` 不得被源值覆盖。
- 不跨 `net_type` 或 `kpi_dim` 强行匹配，除非用户明确要求或结果中清楚说明原因。
- SQL 注释标明源 KPI 名称和源 `kpi_id`；语义匹配补充简短理由。
- 目标行使用 `login_id = NULL`、`visable = 1`、`colored = 1`。
- KPI 行按目标业务字段使用 `WHERE NOT EXISTS` 防重复。
- 颜色行按目标 KPI 实际 `kpi_id` 和区间字段防重复。
- 不臆造缺失的目标 `kpi_name`。

## CSV 导出工作流

1. 使用 `scripts/export_legend_csv.py` 按 `business_name` 查询配置。
2. 在用户提供时继续按 `net_type`、`kpi_dim` 缩小范围。
3. 只导出已返回 KPI 对应的颜色行。
4. 分别输出两张表的 CSV，并使用 UTF-8 BOM。
5. 返回输出路径和行数。

## 安全边界

- 不把密码、令牌或连接串写入 SQL、注释、日志或最终总结。
- 不执行生成的 `INSERT`，不执行 `UPDATE`、`DELETE`、DDL 或可写 CTE。
- 默认生成 Greenplum 兼容 SQL，不使用 `INSERT ... RETURNING`。
- 模糊匹配只作为复核项，不使用固定兜底模板强行生成写入语句。

## 资源

- 使用 [references/usage.md](references/usage.md) 查看输入格式和命令示例。
- 使用 `references/matching-rules.json` 调整归一化词和候选阈值。
- 使用 `scripts/prepare_legend_copy.py` 生成匹配分析与 SQL。
- 使用 `scripts/export_legend_csv.py` 导出 CSV。
