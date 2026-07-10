---
name: convert-excel-to-markdown
description: >
  将 .xlsx、.xlsm、.xltx 或 .xltm 工作簿按 Sheet 转换为 Markdown 表格和索引文件。
  当任务需要导出 Excel、配置表、清单或数据字典为 Markdown 时使用。
---

# Excel 转 Markdown

## 工作流

1. 确认输入工作簿和输出位置。
2. 判断每个 Sheet 的第一行是否为表头；明确时使用 `--first-row-header`。
3. 运行 `scripts/excel_to_markdown.py`。
4. 检查生成的 `README.md`、Sheet 文件名、表格范围和链接。

```bash
python scripts/excel_to_markdown.py "示例.xlsx"
python scripts/excel_to_markdown.py "示例.xlsx" --first-row-header
python scripts/excel_to_markdown.py "示例.xlsx" --out docs/excel-md
```

## 输出规则

- 默认输出到工作簿同级的同名目录。
- 为每个非空 Sheet 生成一个 Markdown 文件。
- 在输出目录生成 `README.md`，记录来源、Sheet 数量、行列数和文档链接。
- 使用安全化后的 Sheet 名作为文件名，并处理安全化后的重名冲突。
- 填充合并区域时使用左上角单元格的值。
- 去除全空的边缘行列，保留表格内部空行和空单元格。
- 不覆盖已有文件，除非用户明确要求并传入 `--overwrite`。

## 边界

- 脚本使用 `openpyxl`，不支持老式 `.xls`；未经用户确认不引入 `xlrd`。
- 默认按脚本现有行为读取单元格值；涉及公式文本或计算结果时，先确认用户需要的口径。
- 隐藏 Sheet 默认按脚本现有行为处理；用户要求排除时再调整输入或脚本选项。
- 大型工作簿可能产生很长的 Markdown；发现输出不可读时，先建议按 Sheet 或主题拆分。
- 特定版式和字段说明优先在转换结果上调整，不把通用脚本改成单一业务解析器。
