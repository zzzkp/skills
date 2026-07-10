---
name: context7-find-docs
description: >
  使用 Context7 检索库、框架、SDK、CLI 工具和云服务的当前文档、API、配置及代码示例。
  当技术问题依赖最新版本、准确函数签名、安装方式或迁移说明时使用。
---

# Context7 文档检索

## 工作流

1. 识别技术名称、供应商、版本和具体问题。
2. 从查询中删除 API key、密码、凭据、个人数据和专有代码。
3. 先解析 Context7 库 ID：

```bash
npx ctx7@latest library <name> "<specific query>"
```

4. 根据名称匹配、任务相关性、来源声誉和版本选择最佳库 ID。
5. 使用选定 ID 查询文档：

```bash
npx ctx7@latest docs /org/project "<specific query>"
```

6. 基于检索结果回答，并说明版本不匹配、资料缺失或未经当前文档验证的部分。

## 查询规则

- 始终先执行 library 查询；用户已提供 `/org/project` 或版本 ID 时可以跳过。
- 使用完整、具体的问题，不使用 `auth`、`hooks`、`config` 等孤立关键词。
- 特定版本存在专属 ID 时优先使用；没有时说明采用的最近版本或最新索引。
- 同一问题默认最多运行三次 Context7 命令；用户明确要求继续时可以追加检索。
- 不默认全局安装 `ctx7`，优先使用 `npx ctx7@latest` 或当前环境已有的最新版本。

## 失败处理

- 配额耗尽时说明原因，并建议用户登录 Context7 获取额度。
- 网络、运行时或安装失败时报告具体错误，不声称结果已经过当前文档验证。
- Context7 没有合适资料时，优先查询该技术的官方文档；仍无可靠来源时再基于通用知识回答并标注时效风险。
- OpenAI 产品和 API 问题优先使用 OpenAI 官方文档能力。
