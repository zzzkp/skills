# 图例配置参考

## 数据库配置

脚本按以下优先级合并数据库配置，后者覆盖前者：

1. skill 根目录下的私有 `local.database.json`。
2. `LEGEND_DB_CONFIG` 指向的 JSON 文件。
3. `LEGEND_DB_*` 环境变量。
4. 输入 JSON 中的 `database` 对象。

支持的环境变量：

- `LEGEND_DB_HOST`
- `LEGEND_DB_PORT`
- `LEGEND_DB_NAME`
- `LEGEND_DB_USER`
- `LEGEND_DB_PASSWORD`
- `LEGEND_DB_SCHEMA`

`local.database.json` 示例：

```json
{
  "host": "127.0.0.1",
  "port": 5432,
  "database": "sqmmt",
  "user": "readonly_user",
  "password": "secret",
  "schema": "tas_master"
}
```

不要在生成 SQL、SQL 注释、分析摘要或最终回复中暴露密码。

## 表结构

`cfg_gis_kpi` 每个模块和指标保存一行图例 KPI 配置。

重要字段：

- `kpi_id`：主标识，颜色配置通过它关联。
- `kpi_name`：目标数据库字段名。缺失时不要臆造。
- `kpi_name_cn`：指标中文展示名，也是主要匹配键。
- `kpi_dim`：KPI 维度，常见值为 `小区`、`栅格`。
- `net_type`：网络类型，常见值为 `4G`、`5G`。
- `kpi_type`：指标类别，如 `覆盖类`、`性能类`、`感知类`。目标输入可用 `kpi_type` 或 `kpiType`，提供后必须覆盖源值。
- `business_name`：模块名，如 `统一GIS` 或目标模块。
- `order_num`：展示顺序。
- `visable`：可见标记。生成目标行固定为 `1`。
- `colored`：是否启用颜色图例。生成目标行固定为 `1`。
- `login_id`：用户范围。生成目标行固定为 `NULL`。

`cfg_gis_kpi_color` 保存一个 KPI 的颜色区间。

重要字段：

- `kpi_id`：关联 `cfg_gis_kpi.kpi_id`。
- `min_value`、`max_value`：图例区间边界。
- `kpi_color`：颜色值。
- `order_num`：颜色区间顺序。

## 匹配优先级

使用最具体、最可辩护的来源匹配：

1. 在相同 `business_name`、`net_type`、`kpi_dim` 范围内精确匹配 `kpi_name_cn`。
2. 使用用户提供的 `search` 源名称，仍受源范围约束。
3. 去除空格、括号单位、百分号和常见词后做归一化名称匹配。
4. 同语义族、同 `net_type`、同 `kpi_dim`，并优先同 `kpi_type`。
5. 只有源模块没有更好候选时，才考虑跨 `kpi_type` 的同语义族候选。
6. 多个候选同样合理或没有接近候选时，输出未解析注释。

归一化、语义族和打分阈值来自 `references/matching-rules.json`。需要新增业务词时优先改这个 JSON，不要直接改脚本逻辑。

AI 语义匹配的 SQL 注释示例：

```sql
-- AI匹配: 目标"网页打开时延"复用"TCP平均建立时延", 原因: 均为时延类指标
```

## AI 候选选择

精确匹配和归一化匹配失败后，检查脚本从全部源模块指标生成的候选列表，选择最适合目标 KPI 的来源。

优先选择：

- `net_type`、`kpi_dim`、`kpi_type` 相同的候选。
- 语义族相同的候选，如时延、成功率、掉线掉话、流量、速率、覆盖、干扰、重建。
- 测量对象和方向相近的候选，如上行/下行、TCP/HTTP/视频/网页、小区/栅格、用户/小区。
- 数值含义和颜色阈值方向兼容的候选。不要把“越高越差”的图例复制给“越高越好”的 KPI，除非颜色区间明显仍然适用。
- 已有颜色行的候选，前提是目标 KPI 需要着色。

拒绝或保持未解析：

- 候选只共享 `率` 等泛词，但业务含义不同。
- 多个候选同样可能且用户没有提供足够上下文。
- 目标缺少 `kpi_name`。
- 同范围存在候选，但跨 `net_type` 或跨 `kpi_dim` 的候选只是弱相关。

选择候选时，在决策 JSON 或 SQL 注释中写简短原因。

## SQL 生成规则

- 生成带 `BEGIN;` 和 `COMMIT;` 的事务 SQL 文件。
- 默认兼容 Greenplum。
- 先插入 `cfg_gis_kpi`，再插入 `cfg_gis_kpi_color`。
- 不使用可写 CTE、数据修改型 `WITH` 或 `INSERT ... RETURNING`。
- 新 KPI 行使用确定性的 `YYYYMMDD` 加三位序号作为候选 `kpi_id`，但颜色插入不依赖该候选值。
- KPI 行通过目标业务字段防重复：`business_name`、`net_type`、`kpi_dim`、`kpi_name`。
- 颜色行通过目标业务字段先查询目标实际 `kpi_id`，再按 `min_value`、`max_value`、`kpi_color`、`order_num` 防重复。
- 用户提供的目标字段优先；缺失的可选字段从源 KPI 复制。
- `kpi_type` 接受 `kpi_type` 或 `kpiType`，提供后不得复制源 `kpi_type`。
- 目标 `login_id` 固定为 `NULL`，`visable` 固定为 `1`，`colored` 固定为 `1`。
- 源有颜色行时复制颜色行；源没有颜色行时输出注释说明。
- SQL 字符串字面量使用单引号转义。
- 未解析 KPI 输出注释，不生成不完整插入语句。

## CSV 导出规则

- `cfg_gis_kpi` 和 `cfg_gis_kpi_color` 分别导出为两个 CSV。
- `cfg_gis_kpi` 先按 `business_name` 过滤；用户提供 `net_type`、`kpi_dim` 时继续缩小范围。
- `cfg_gis_kpi_color` 只导出过滤后的 KPI 对应颜色行。
- CSV 字段顺序固定：
  - `cfg_gis_kpi`：`kpi_id, net_type, kpi_dim, kpi_type, kpi_name, kpi_name_cn, order_num, visable, colored, business_name, login_id`
  - `cfg_gis_kpi_color`：`kpi_id, min_value, max_value, kpi_color, order_num`
- 使用 UTF-8 BOM，即 `utf-8-sig`，方便 Windows 工具打开。
- 导出必须只读，不执行 insert、update、delete、DDL 或任何修改数据的辅助 SQL。
