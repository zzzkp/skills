---
name: git-create-commit
description: >
  检查 Git 工作区和暂存区、选择本次任务文件、编写提交信息并在用户明确要求时创建 commit。
  当用户要求准备提交、生成 commit message、暂存相关文件或执行 git commit 时使用。
---

# Git 提交

## 意图边界

- 用户只要求查看状态时，只检查并报告，不暂存或提交。
- 用户只要求提交信息时，只生成 message，不修改暂存区。
- 用户要求准备提交时，可以检查和暂存本次任务文件，但不自动提交。
- 只有用户明确要求提交时才执行 `git commit`。
- 本 Skill 不执行 push；用户另行明确要求时再单独处理。

## 工作流

1. 使用 `git status --short` 区分 staged、unstaged 和 untracked 文件。
2. 使用 `git diff` 和 `git diff --staged` 检查实际变更和已有暂存内容。
3. 识别本次任务文件，保留并避开用户的无关改动。
4. 先查看仓库近期提交，优先遵循已有提交语言和格式。
5. 只暂存属于本次任务且用户授权纳入提交的文件。
6. 创建描述提交后行为的 message；需要时补充原因、取舍或迁移说明。
7. 提交前重新检查暂存区；用户明确要求后执行 `git commit`。
8. 提交完成后报告 commit hash 和完整 message。

## Commit Message

优先使用：

```text
<type>(<scope>): <中文摘要>
```

- 使用仓库已有约定；没有明确约定时再采用 Conventional Commits。
- `type` 可使用 `feat`、`fix`、`refactor`、`test`、`docs`、`build` 或 `chore`。
- 摘要使用具体的中文动宾短语，不写“更新代码”等模糊内容。
- 尽量控制在 72 个字符以内，末尾不加句号。
- 只有摘要无法说明原因、重要取舍或风险时才添加正文。

## 安全规则

- 不运行 `git reset --hard`、`git checkout --`、强制推送等破坏性命令，除非用户明确授权。
- 不回退或覆盖用户的现有改动。
- 不提交密钥、环境配置、编辑器文件、依赖缓存或无关生成物。
- 工作区包含多个任务且无法可靠拆分时，暂停并向用户确认。
- pre-commit hook 修改文件后，重新检查差异和暂存区。
