---
name: doc
description: >
  DOCX 和 Word 文档处理，读取、创建、编辑、审阅 .docx 文档并尽量保留格式和布局。
  当用户要求读取 Word、修改 Word、创建 DOCX、审阅文档、处理 Word 表格或检查文档排版时使用。
  触发关键词：DOCX、Word、.docx、读取 Word、修改 Word、创建 Word、编辑文档、文档审阅、表格、页眉页脚、分页、格式保留、布局检查、python-docx、可视化检查、专业文档排版。
---

# DOCX 技能

## 适用场景
- 读取或审阅需要关注布局的 DOCX 内容，例如表格、图示和分页。
- 创建或编辑具有专业格式的 DOCX 文件。
- 交付前验证可视化布局。

## 工作流
1. 优先进行可视化审阅，包括布局、表格和图示。
   - 如果 `soffice` 和 `pdftoppm` 可用，将 DOCX 转为 PDF，再转为 PNG。
   - 或使用 `scripts/render_docx.py`，该脚本需要 `pdf2image` 和 Poppler。
   - 如果缺少这些工具，安装它们，或请用户在本地审阅渲染后的页面。
2. 使用 `python-docx` 进行编辑和结构化创建，例如标题、样式、表格和列表。
3. 每次有实质性修改后，重新渲染并检查页面。
4. 如果无法进行可视化审阅，使用 `python-docx` 提取文本作为备用方式，并明确说明布局风险。
5. 保持中间输出有序，并在最终确认后清理。

## 临时目录与输出约定
- 使用 `tmp/docs/` 存放中间文件；完成后删除。
- 在本仓库内工作时，将最终产物写入 `output/doc/`。
- 文件名保持稳定且具备描述性。

## 依赖项（缺失时安装）
优先使用 `uv` 管理依赖。

Python 包：
```
uv pip install python-docx pdf2image
```
如果 `uv` 不可用：
```
python3 -m pip install python-docx pdf2image
```
用于渲染的系统工具：
```
# macOS (Homebrew)
brew install libreoffice poppler

# Ubuntu/Debian
sudo apt-get install -y libreoffice poppler-utils
```

如果当前环境无法安装，告诉用户缺少哪个依赖，以及如何在本地安装。

## 环境
不需要环境变量。

## 渲染命令
DOCX 转 PDF：
```
soffice -env:UserInstallation=file:///tmp/lo_profile_$$ --headless --convert-to pdf --outdir $OUTDIR $INPUT_DOCX
```

PDF 转 PNG：
```
pdftoppm -png $OUTDIR/$BASENAME.pdf $OUTDIR/$BASENAME
```

内置辅助脚本：
```
python3 scripts/render_docx.py /path/to/file.docx --output_dir /tmp/docx_pages
```

## 质量要求
- 交付可直接面向客户的文档：排版、间距、页边距保持一致，层级清晰。
- 避免格式缺陷：文本裁切或重叠、表格破损、字符不可读、默认模板样式明显残留。
- 图表、表格和视觉元素必须在渲染页面中清晰可读，并且对齐正确。
- 仅使用 ASCII 连字符。避免使用 U+2011（不换行连字符）和其他 Unicode 破折号。
- 引文和参考文献必须便于人工阅读；不得留下工具令牌或占位字符串。

## 最终检查
- 最终交付前重新渲染，并以 100% 缩放检查每一页。
- 修复所有间距、对齐或分页问题，并重复渲染检查流程。
- 确认没有遗留文件，例如临时文件或重复渲染文件，除非用户要求保留。
