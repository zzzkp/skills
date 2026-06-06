---
name: git
description: Git 提交工作流指南。用于用户要求提交代码、创建 git commit、提交变更、编写 commit message、修改提交，或在提交前检查 staged 和 unstaged 变更的场景。
---

# Git

## 工作流

在准备仓库提交时使用此 skill。

1. 使用 `git status --short` 检查仓库状态，区分 staged、unstaged 和 untracked 文件。
2. 使用 `git diff` 和 `git diff --staged` 查看实际变更。如果存在无关的用户改动，除非用户明确要求，不要纳入提交，也不要回退。
3. 判断用户要求的工作是否已经达到可提交状态。如果必要检查没有运行，应在最终回复中说明。
4. 只 stage 属于本次请求的文件。
5. 编写描述提交后行为的 commit message，不要只描述实现杂项。
6. 使用 `git commit -m "<subject>"` 提交；如果变更需要额外上下文，再添加提交正文。

## Commit Message 编写

编写 commit message 时，优先使用当前会话上下文中的信息，包括用户请求、已完成的修改、已说明的实现结果和已观察到的验证情况。只有在没有当前会话上下文，或上下文不足以判断提交意图时，才使用 `git diff` / `git diff --staged` 补充分析 message。

优先使用简洁的 subject：

```text
<type>(<scope>): <summary>
```

只有在 scope 能提供有效上下文时才使用。

常见 type：

- `feat`：新增或调整用户可感知的功能。
- `fix`：修复缺陷或回归问题。
- `refactor`：调整代码结构，但不改变预期行为。
- `test`：新增或更新测试。
- `docs`：仅修改文档。
- `build`：构建系统、依赖、打包或 CI 相关变更。
- `chore`：不属于以上类型的维护性变更。

Subject 规则：

- 使用祈使语气：写 `fix login redirect`，不要写 `fixed login redirect`。
- 尽量控制在 72 个字符以内。
- 末尾不要加句号。
- 说明具体结果：写 `fix monthly report date filter`，不要写 `update code`。
- 如果仓库近期提交已经有明确风格，应优先保持一致。

只有当 subject 无法充分说明变更时才添加 body。body 用于说明变更原因、重要取舍、迁移注意事项或风险。正文每行尽量控制在 72 个字符左右。

示例：

```text
feat(report): add monthly export action
fix(auth): preserve redirect after session refresh
refactor(import): split workbook parsing from validation
docs: update deployment variables
chore: refresh generated config
```

## 安全规则

- 除非用户明确要求对应操作，否则不要运行 `git reset --hard`、`git checkout --`、强制推送等破坏性 git 命令。
- 不要提交密钥、本地环境文件、编辑器文件、依赖缓存，或不属于本次请求的生成产物。
- 如果工作区包含多个任务的变更，只提交本次请求相关文件；无法明确拆分时，先询问用户。
- 如果 pre-commit hook 修改了文件，提交前重新检查 diff。
- 提交完成后，报告 commit hash 和 commit message。
