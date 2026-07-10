# DOCX 渲染

## 工具检查

优先检查当前环境是否已有 LibreOffice、Poppler、`python-docx` 和 `pdf2image`。缺失依赖时先说明影响并获得用户授权，不自动安装。

## LibreOffice 与 Poppler

DOCX 转 PDF：

```bash
soffice --headless --convert-to pdf --outdir <output-dir> <input.docx>
```

PDF 转 PNG：

```bash
pdftoppm -png <input.pdf> <output-prefix>
```

## 内置脚本

确认 `pdf2image` 和 Poppler 可用后运行：

```bash
python scripts/render_docx.py <input.docx> --output_dir <output-dir>
```

渲染后逐页检查文本裁切、重叠、分页、表格、图片和页眉页脚。无法渲染时使用文本提取作为降级方式，并在交付时说明布局未经过可视化验证。
