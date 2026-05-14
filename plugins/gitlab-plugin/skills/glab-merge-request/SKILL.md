---
name: glab-merge-request
description: 用于创建 GitLab Merge Request 的工作流技能。
disable-model-invocation: true
allowed-tools:
  - Bash(git push *)
  - Bash(git commit *)
  - Bash(glab *)
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# GitLab Merge Request 创建工作流

当用户需要将当前分支推送到 GitLab 并发起合并请求时使用。自动处理分支保护、代码提交和 MR 创建的全流程。

快速完成从代码变更到 MR 创建的完整流程。

## 前置条件检查

**检查 glab 是否已安装：**
```bash
which glab || echo "NOT_INSTALLED"
```

若未安装，提示用户：
```
glab 未安装，请运行以下命令安装：
  brew install glab
或参考：https://gitlab.com/gitlab-org/cli/-/blob/main/docs/installation_options.md
```

**检查 glab 是否已登录：**
```bash
glab auth status
```

若未登录，提示用户：
```
请先登录 GitLab：
  glab auth login --hostname <gitlab.example.org> --token <your-token>
```

## 执行步骤

### 步骤 1：确保在合适的分支

检查当前分支：
```bash
git branch --show-current
```

若当前分支是 `main` 或匹配 `dev-*` 模式，则自动创建新的个人分支：
```bash
# 获取 git 用户名
AUTHOR=$(git config user.name | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
RANDOM_SUFFIX=$(openssl rand -hex 3)
BRANCH_NAME="mr-${AUTHOR}-${RANDOM_SUFFIX}"
git checkout -b "$BRANCH_NAME"
```

若已在个人功能分支（非 main/dev-*），则直接继续。

### 步骤 2：提交代码变更

检查 staged 状态：
```bash
git status --short
```

- **若有 staged 文件**（`git diff --cached --stat` 有输出）：直接调用 `/commit` 命令提交
- **若没有 staged 文件但有变更文件**：执行 `git add .` 后再调用 `/commit` 命令提交
- **若没有任何变更**：跳过提交步骤，直接创建 MR

### 步骤 3：创建 Merge Request

```bash
glab mr create -f --push --no-editor --create-source-branch -b main --fill --remove-source-branch -y
```

参数说明：
- `-f` / `--force`：若 MR 已存在则强制更新
- `--push`：自动推送当前分支到远程
- `--no-editor`：不打开编辑器，直接创建
- `--create-source-branch`：若远程分支不存在则自动创建
- `-b main`：目标分支为 main
- `--remove-source-branch`：MR 合并后自动删除源分支

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| glab 未安装 | 提示安装命令，停止执行 |
| glab 未登录 | 提示登录命令，停止执行 |
| 无远程仓库 | 提示用户先配置 remote |
| 提交失败 | 显示错误信息，询问是否继续 |