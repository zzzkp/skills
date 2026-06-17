---
name: find-docs
description: >
  使用 Context7 检索开发技术的最新文档、API 参考、配置说明和代码示例。
  当用户要求查询库、框架、SDK、CLI 工具、云服务的当前 API、安装方式、配置项、版本迁移或调试问题时使用。
  触发关键词：Context7、最新文档、官方文档、API reference、代码示例、配置选项、版本迁移、安装说明、调试问题、React、Next.js、Prisma、Express、Tailwind、Django、Spring Boot、不要凭记忆回答。
---

# 查找文档

使用 Context7 检索开发技术的最新文档和示例。对于 API 细节、函数签名、配置、迁移、安装和 CLI 用法，优先使用当前文档，而不是记忆。

## 工作流

1. 识别用户请求中的库、框架、SDK、CLI 工具或云服务。
2. 从查询中移除敏感或机密信息，包括 API key、密码、凭据、个人数据和专有代码。
3. 先解析库 ID：

```bash
npx ctx7@latest library <name> "<specific query>"
```

4. 从结果中选择最合适的 Context7 库 ID。
5. 使用选定的 ID 查询文档：

```bash
npx ctx7@latest docs /org/project "<specific query>"
```

只有在已安装 `ctx7`，或已经更新后，才使用本地安装的 `ctx7` 二进制文件：

```bash
npm install -g ctx7@latest
ctx7 library <name> "<specific query>"
ctx7 docs /org/project "<specific query>"
```

## 必要查询规则

- 始终先调用 `ctx7 library`，再调用 `ctx7 docs`，除非用户明确提供 `/org/project` 或 `/org/project/version` 格式的 Context7 库 ID。
- 始终向 `ctx7 library` 传入描述性查询参数；使用用户意图区分名称相近的包。
- 针对同一个用户问题，Context7 命令最多运行 3 次。如果 3 次后答案仍不完整，使用已有最佳结果，并说明限制。
- 当不确定 CLI 是否已安装时，优先使用 `npx ctx7@latest`，避免依赖过期的全局安装。
- 不要在 Context7 查询中包含敏感信息。

## 选择库 ID

按以下信号选择最相关的匹配项，优先级从高到低：

1. 与用户请求技术的名称完全匹配或接近匹配。
2. 描述与用户任务的相关性。
3. 更高的代码片段覆盖量。
4. High 或 Medium 来源声誉。
5. 更高的基准评分。

如果存在多个强匹配项，简要说明歧义，并使用最佳匹配继续。如果没有合理匹配项，说明 Context7 没有返回合适结果，并请用户提供更具体的包名、供应商或库 ID。

## 版本处理

如果用户请求特定版本，并且 `ctx7 library` 输出中存在版本专属 ID，则使用该 ID：

```bash
npx ctx7@latest docs /org/project/version "<specific query>"
```

如果没有精确版本，使用列出的最接近版本，并说明选择。如果没有合适版本，使用最新索引 ID，并说明没有可用的版本专属文档。

## 查询质量

尽可能使用用户的完整问题。优先使用具体查询，例如：

```bash
npx ctx7@latest library react "React useEffect cleanup function with async operations"
npx ctx7@latest docs /facebook/react "React useEffect cleanup function with async operations"
```

避免 `auth`、`hooks` 或 `config` 等模糊的单词查询。

## 错误处理

如果 Context7 因 `Monthly quota reached` 或 `quota exceeded` 等配额错误失败：

1. 告诉用户他们的 Context7 配额已耗尽。
2. 建议使用 `ctx7 login` 获得更高额度。
3. 如果用户无法认证，必须先明确说明当前文档不可用、答案可能过时，然后才能基于通用知识回答。

如果 Context7 因网络或安装原因失败，报告失败原因；仅在有帮助时继续回答，并明确标注该答案未经过当前文档验证。
