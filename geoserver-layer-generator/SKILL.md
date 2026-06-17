---
name: geoserver-layer-generator
description: >
  GeoServer 图层、SQL 与 SLD 样式生成器，根据业务查询 SQL 制作地图图层查询和样式文件。
  当用户要求生成或改写 GeoServer 图层、PostGIS 几何查询、SQL 图层、WMS/WFS 地图服务或点线面样式时使用。
  触发关键词：GeoServer、SQL 图层、地图图层 SQL、SLD、SLD XML、PostGIS、geometry、geom、GeoJSON、WMS、WFS、点样式、线样式、面样式、图层配置、SQL 加样式文件。
---

# GeoServer 图层生成器

## 目标

用于根据用户提供的一段查询 SQL 和图层需求，整理出 GeoServer 可用的 SQL 图层查询，并生成匹配的 SLD XML 样式。重点是保留用户原始业务查询意图，同时补齐 GeoServer 图层所需的 `gid`、`geom`、参数过滤和点线面样式。

## 输入检查

开始处理前，尽量从用户提供的 SQL 和图层说明中确认以下信息：

- `input_sql`：用户提供的原始查询 SQL。
- `layer_name`：图层名或文件名主干；用户未提供时，根据业务含义生成小写 ASCII 名称。
- `geometry_type`：`polygon`、`line` 或 `point`。
- `geometry_source`：GeoJSON 文本、已有 geometry 字段，或经纬度字段。
- `geometry_field`：GeoJSON/geometry 字段名，或 `longitude`、`latitude` 字段名。
- `id_field`：可作为稳定 `gid` 的字段或表达式。
- `filters`：需要保留或新增的 GeoServer view parameters，例如 `city`、`area`、`name`、`categoryType`。
- `style`：颜色、线宽、点大小、是否只描边。
- `output_target`：用户是否需要落盘到具体文件；未说明时，直接输出 SQL 和 SLD 内容。

缺少非关键字段时，可从 SQL 字段名、图层说明和常见 GIS 命名推断；缺少几何来源或几何类型时，应先向用户确认。

## 工作流

1. 阅读用户给出的原始 SQL，识别 SELECT 字段、主表/子查询、过滤条件、排序/分组和可能的几何字段。
2. 判断原始 SQL 是否已经包含稳定 ID 和几何输出；没有则按规则补齐 `gid` 和 `geom`。
3. 将需要暴露给 GeoServer 的筛选条件改写为 view parameter 形式，例如 `'%city%' = '' OR a.city = '%city%'`。
4. 根据图层类型生成匹配的 SLD：面、线或点。
5. 用户指定文件路径时，只创建或更新请求的 SQL 和 SLD 文件；否则直接输出可复制的 SQL 和 XML。
6. 不执行 SQL、不连接数据库、不编译、不运行测试，除非用户明确要求。

## SQL 规则

默认遵循以下规则：

- 输出稳定的 `gid` 列和名为 `geom` 的 PostGIS 几何列。
- GeoServer 输出几何保持 EPSG:4326。
- GeoJSON 文本使用 `ST_SetSRID(ST_GeomFromGeoJSON(<field>), 4326)`。
- 已有 geometry 字段如果不是 4326，使用 `ST_Transform(<field>, 4326)`。
- 经纬度字段使用 `ST_SetSRID(ST_MakePoint(<longitude>, <latitude>), 4326)`。
- GeoServer view parameters 直接内联，例如 `'%city%' = '' OR a.city = '%city%'`。
- 不使用参数 CTE，例如 `WITH p AS (...)` 或 `CROSS JOIN p`。
- 不使用 `NULLIF` 或 `IS NULL` 判断参数是否为空；使用空字符串判断。
- 不在 filter 或 join 中强转表字段；必须强转时，强转参数侧。
- 只有在聚合、计算或去重逻辑明显更清晰时，才保留业务 CTE。
- 实际可行时过滤无效几何来源，例如非空 GeoJSON 文本、非空经纬度。

从零开始或需要重组用户 SQL 时，使用 `assets/layer.sql.template`。需要更贴近类型的参考时，读取 `assets/examples/` 下的示例：

- `polygon_geojson.sql`
- `line_geometry.sql`
- `point_lon_lat.sql`

## 几何表达式选择

按来源选择 `geom` 表达式：

- GeoJSON polygon/line/point：`ST_SetSRID(ST_GeomFromGeoJSON(a.<geojson_field>), 4326) AS geom`
- 已有 geometry 且 SRID 已是 4326：`a.<geom_field> AS geom`
- 已有 geometry 且 SRID 不是 4326：`ST_Transform(a.<geom_field>, 4326) AS geom`
- 经纬度字段：`ST_SetSRID(ST_MakePoint(a.<longitude_field>, a.<latitude_field>), 4326) AS geom`

常见有效性过滤：

- GeoJSON：`a.<geojson_field> IS NOT NULL AND a.<geojson_field> <> ''`
- geometry：`a.<geom_field> IS NOT NULL`
- 经纬度：`a.<longitude_field> IS NOT NULL AND a.<latitude_field> IS NOT NULL`

## SQL 验收标准

生成或修改 SQL 后，人工检查：

- SELECT 中存在 `gid` 和 `geom`。
- `geom` 明确输出为 EPSG:4326。
- 参数过滤使用 `'%param%' = '' OR ...`。
- `name` 等模糊搜索优先保留用户原 SQL 语义；无明确写法时使用 `LIKE concat('%%', '%name%', '%%')`。
- 没有参数 CTE、无意义 CTE、字段侧 cast、数据库连接语句或执行语句。
- 文件名为 `<layer_name>.sql`。

## SLD 规则

生成 GeoServer 兼容的 SLD 1.0.0 XML：

- SLD `<Name>` 使用样式文件主干，例如 `cg_scene_manage_scene_style`。
- SLD `<Title>` 与 `<Name>` 保持一致，除非用户指定展示名称。
- 面图层使用 `PolygonSymbolizer`。
- 线图层使用 `LineSymbolizer`。
- 点图层使用 `PointSymbolizer`。
- 只显示边界的面：`fill-opacity` 为 `0`，可见颜色放在 `Stroke`。
- 样式保持简单、可移植；除非用户确认环境支持，否则避免 GeoServer vendor functions。
- 用户要求线加顶点标记等复杂效果时，先给稳定单层样式；确有必要时再建议第二图层。

从零开始时使用 `assets/style.xml.template`。需要类型参考时，读取：

- `assets/examples/polygon_boundary_style.xml`
- `assets/examples/line_style.xml`
- `assets/examples/point_style.xml`

## SLD 验收标准

生成或修改 SLD 后，人工检查：

- XML 声明和 SLD 1.0.0 命名空间完整。
- `<Name>`、`<Title>` 与文件名主干一致。
- Symbolizer 与几何类型匹配。
- 颜色为十六进制 CSS 色值，例如 `#44b3f7`。
- 面边界样式没有误把填充设为可见。
- 文件名为 `<layer_name>_style.xml`。

## 命名规则

默认命名模式：

- SQL：`<layer_name>.sql`
- 样式：`<layer_name>_style.xml`
- 样式 `<Name>` 和 `<Title>`：`<layer_name>_style`

未提供 `layer_name` 时，优先根据 SQL 主表、业务字段或用户描述生成小写 ASCII 标识符，例如 `scene_boundary`、`road_segment`、`monitor_site`。
