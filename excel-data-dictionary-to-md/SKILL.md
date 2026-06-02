---
name: excel-data-dictionary-to-md
description: Convert Excel data dictionaries and database table field lists, especially Chinese .xlsx files such as "5G高倒流分析-数据字典.xlsx", into Markdown documentation. Use when Codex needs to parse an Excel data dictionary, generate one Markdown file per table, and create a README overview with table links, field counts, source sheets, and table descriptions.
---

# Excel Data Dictionary To Markdown

Use this skill to convert an Excel data dictionary into Markdown documentation.

## Workflow

1. Locate the input `.xlsx` file.
2. Run `scripts/excel_dict_to_md.py` with the Excel path and an output directory.
3. Review the generated `README.md` and per-table Markdown files.
4. If field columns are missing, inspect the Excel headers and extend the alias lists in the script.

Example:

```bash
python scripts/excel_dict_to_md.py "5G高倒流分析-数据字典.xlsx" --out docs/data-dictionary
```

## Output Rules

- Generate one Markdown file per detected table.
- Generate one `README.md` overview in the output directory.
- Keep original table names and Chinese labels in document titles.
- Sanitize file names for filesystem safety.
- Use source sheet names in generated metadata.
- Skip empty sheets and obvious non-dictionary sheets such as covers, catalogs, changelogs, and version records.

## Parser Expectations

The bundled script uses `openpyxl` and handles:

- Chinese and English field header aliases.
- Merged cell values by filling merged ranges.
- One table per sheet.
- Multiple table blocks in one sheet separated by title rows or repeated field headers.
- Common metadata labels such as table name, Chinese name, description, comment, and remark.

Prefer updating the script's alias lists instead of rewriting parsing logic when a workbook uses different column names.
