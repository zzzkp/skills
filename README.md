# ZZZKP Skills

面向 Codex 与 Claude Code 的可复用 Agent Skills 合集。仓库采用公共 `SKILL.md`、双平台插件清单的组织方式：工作流正文和资源只维护一份，Codex 与 Claude Code 分别读取自己的插件元数据。

## 仓库结构

```text
.agents/plugins/marketplace.json              # Codex Marketplace
.claude-plugin/marketplace.json               # Claude Code Marketplace
plugins/zzzkp-skills/
├── .codex-plugin/plugin.json                 # Codex 插件清单
├── .claude-plugin/plugin.json                # Claude Code 插件清单
└── skills/
    └── <skill-name>/
        ├── SKILL.md                          # 两个平台共用
        ├── agents/openai.yaml                # Codex 界面元数据
        ├── scripts/                          # 按需提供
        ├── references/                       # 按需提供
        └── assets/                           # 按需提供
```

## Skills

| Skill | 用途 |
| --- | --- |
| `copy-gis-legend-config` | 复制、迁移和导出 GIS 图例及指标颜色配置 |
| `convert-daily-reports-to-monthly-report` | 将日报明细汇总为月报正文和工时天数统计 |
| `manage-docx` | 创建、编辑、审阅和检查 DOCX 文档 |
| `convert-excel-to-markdown` | 将 Excel 工作簿按 Sheet 转换为 Markdown |
| `context7-find-docs` | 使用 Context7 检索当前开发技术文档 |
| `develop-web-ui` | 开发和重构 Web 页面、组件及交互逻辑 |
| `generate-geoserver-layer` | 生成 GeoServer SQL 图层和 SLD 样式 |
| `git-create-commit` | 检查变更范围并创建规范 Git 提交 |
| `summarize-gitlab-work` | 根据指定周期的 GitLab 提交生成中文工作记录 |
| `develop-java-backend` | 开发和重构 Java 后端接口及业务服务 |
| `manage-project-docs` | 维护项目 Markdown 文档和知识库索引 |

## 公共 Skill 规范

每个 `SKILL.md` 的 YAML frontmatter 只声明 `name` 和 `description`，作为 Codex 与 Claude Code 的公共最小规范。

Codex 专属的展示名称、简介、图标和默认提示放在 `agents/openai.yaml`。Claude Code 专属的插件信息放在 `.claude-plugin/`，不向公共 `SKILL.md` 添加 `allowed-tools`、`argument-hint` 等平台字段。

## 安装到 Codex

先克隆仓库：

```bash
git clone https://github.com/zzzkp/skills.git
```

添加仓库 Marketplace 并安装插件：

```bash
codex plugin marketplace add <repository-path>
codex plugin add zzzkp-skills@zzzkp
```

安装或更新后，开启新的 Codex 会话以加载 Skills。

## 安装到 Claude Code

在 Claude Code 中添加 Marketplace 并安装插件：

```text
/plugin marketplace add <repository-path>
/plugin install zzzkp-skills@zzzkp
```

插件中的 Skill 使用插件名称作为命名空间，例如：

```text
/zzzkp-skills:manage-docx
/zzzkp-skills:git-create-commit
```

## 单独安装 Skill

Codex 可以使用 `$skill-installer` 安装仓库中的单个 Skill：

```text
$skill-installer install https://github.com/zzzkp/skills/tree/main/plugins/zzzkp-skills/skills/manage-docx
```

Claude Code 可以将同一 Skill 目录复制到项目 `.claude/skills/` 或用户目录 `~/.claude/skills/`。公共 `SKILL.md`、`scripts/`、`references/` 和 `assets/` 均可直接复用。
