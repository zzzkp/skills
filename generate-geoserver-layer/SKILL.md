---
name: generate-geoserver-layer
description: >
  根据业务查询 SQL 生成或改写 GeoServer SQL 图层查询和 SLD 1.0.0 样式。
  当任务涉及 PostGIS 几何、GeoJSON、经纬度、WMS/WFS、View Parameter 或点线面样式时使用。
---

# GeoServer 图层生成

## 必要输入

- 确认原始查询 SQL、图层业务含义和输出方式。
- 确认几何类型为 `polygon`、`line` 或 `point`。
- 确认几何来源为 GeoJSON、已有 geometry 字段或经纬度字段。
- 确认稳定唯一的 ID 字段、需要暴露的 View Parameter 和样式要求。
- 缺少几何来源或几何类型时先向用户确认；其他非关键字段可以根据上下文推断并说明。

## 工作流

1. 分析原始 SQL 的字段、表、过滤、聚合、排序和几何来源。
2. 保留原始业务语义，补齐稳定唯一的 `gid` 和名为 `geom` 的几何列。
3. 将需要暴露的条件改写为 GeoServer View Parameter，并为每个参数提供默认值和校验表达式。
4. 根据几何类型生成 SLD 1.0.0 样式。
5. 用户指定路径时只写入请求的 SQL 和 SLD 文件；否则返回可复制内容。
6. 人工检查 SQL、参数、几何类型、SRID、XML 和文件命名。

## SQL 规则

- 输出稳定唯一的 `gid`，避免使用结果顺序或不稳定窗口编号作为长期标识。
- 输出名为 `geom` 的 PostGIS 几何，并统一为 EPSG:4326。
- GeoJSON 使用 `ST_SetSRID(ST_GeomFromGeoJSON(<field>), 4326)`。
- 非 4326 geometry 使用 `ST_Transform(<field>, 4326)`。
- 经纬度使用 `ST_SetSRID(ST_MakePoint(<longitude>, <latitude>), 4326)`。
- 过滤空 GeoJSON、空 geometry 或空经纬度。
- 不在字段侧做不必要的强制转换；必须转换时优先转换参数侧。
- 只在聚合或计算明显更清晰时保留业务 CTE，不创建参数 CTE。
- 不连接数据库、不执行 SQL，除非用户明确要求。

## View Parameter 安全

- 为每个参数定义明确默认值和允许格式，不接受任意 SQL 片段。
- 字符串参数限制长度和字符集合；枚举参数限制为允许值；数字参数只允许数字格式。
- 参数内联保持 GeoServer SQL View 语法，但不得移除 GeoServer 侧的正则校验。
- 模糊查询保留原 SQL 语义；没有明确语义时再使用包含匹配。

## SLD 规则

- 生成完整的 SLD 1.0.0 XML 和命名空间。
- 面、线、点分别使用 `PolygonSymbolizer`、`LineSymbolizer`、`PointSymbolizer`。
- 只显示边界的面将 `fill-opacity` 设为 `0`，颜色放在 `Stroke`。
- 使用十六进制 CSS 色值，避免未经确认的 GeoServer vendor function。
- `<Name>`、`<Title>` 和文件主干保持一致。

## 命名与资源

- SQL 文件命名为 `<layer_name>.sql`。
- 样式命名为 `<layer_name>_style.xml`。
- 使用 `assets/layer.sql.template` 和 `assets/style.xml.template` 创建输出。
- 需要点线面示例时，按任务读取 `references/` 下对应的 SQL 或 XML 文件。
