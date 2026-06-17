---
name: excel2md
description: >
  Excel 转 Markdown 与工作簿导出，将 .xlsx / .xlsm 工作簿按 Sheet 转为 Markdown 表格。
  当用户要求把 Excel、工作簿、配置表、清单表或数据字典转换为 Markdown、README 或按 Sheet 导出时使用。
  触发关键词：Excel 转 Markdown、xlsx、xlsm、工作簿、Sheet、表格导出、Markdown 表格、README、合并单元格、中文表格、配置表、数据字典、清单整理。
---

# Excel 转 Markdown

使用此技能将 Excel 工作簿转换为 Markdown 文档。

## 工作流

1. 定位输入 Excel 文件。
2. 根据表格结构选择转换方式：
   - 默认模式：生成 `A`、`B`、`C` 等列头，并把 Excel 中的所有非空区域行作为数据保留。
   - 如果每个 Sheet 的第一行就是表头，添加 `--first-row-header`。
3. 运行 `scripts/excel2md.py`，传入 Excel 路径；如需指定位置，再传入 `--out`。
4. 检查输出目录中的 `README.md` 和各 Sheet 对应的 Markdown 文件。

示例：

```bash
python scripts/excel2md.py "示例.xlsx"
python scripts/excel2md.py "示例.xlsx" --first-row-header
python scripts/excel2md.py "示例.xlsx" --out docs/excel-md
```

## 输出规则

- 默认输出到 Excel 同级的源文件同名目录，例如 `示例.xlsx` 输出到 `示例/`。
- 为每个非空 Sheet 生成一个 Markdown 文件。
- 在输出目录生成一个 `README.md`，索引全部 Sheet 文件，并汇总来源文件、Sheet 数量、行列数和文档链接。
- 使用 Sheet 名作为 Markdown 文件名，并进行文件名安全化处理。
- 填充合并单元格区域，使用合并区域左上角的值。
- 去掉全空的边缘行列，保留表格内部空行和空单元格。
- 不覆盖已有文件，除非传入 `--overwrite`。

## 使用约束

- 脚本使用 `openpyxl`，支持 `.xlsx`、`.xlsm`、`.xltx`、`.xltm`。
- 不支持老式 `.xls`；除非用户明确允许新增依赖，否则不要主动引入 `xlrd`。
- 如果用户要求特定版式、标题层级或字段说明格式，优先在转换后按需求调整 Markdown，而不是把通用脚本改回专用解析器。
