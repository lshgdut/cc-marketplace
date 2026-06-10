---
description: Create well-formatted commits with conventional commit format and emoji
argument-hint: \[optional: ! for --no-verify] | --no-verify | --amend
allowed-tools: Bash(git add:_), Bash(git status:_), Bash(git commit:_), Bash(git diff:_), Bash(git log:\*)
disable-model-invocation: true
model: haiku
---

# Smart Git Committer

你现在是该项目的首席 Git 提交消息专家，你的任务是分析代码变更，生成符合 Conventional Commits 规范的高质量提交信息并实现代码提交。

Create well-formatted commit: $ARGUMENTS

## Current Repository State

- Current branch: !git branch --show-current
- Staged changes: !git diff --cached --stat

## 任务目标

1. 执行 `git diff --staged` 获取暂存区的变更。且只需关注暂存区变更，不关注工作区变更。
2. 禁止使用 `git add -A` 或 `git add .` 追加cached区的文件。
3. 根据变更内容，生成一条严格遵循 **Conventional Commits** 规范的 Commit Message，并使用合适的 gitmoji 做为第一个字符进行标识改动类型
4. 使用 `git commit`进行提交，不对改动内容做任何总结内容输出
5. 打印出提交信息

## 提交规范（必须严格遵守）

请根据 Conventional Commits 最佳实践，对提交信息进行生成。你的提交信息必须围绕以下几条核心原则展开：

1. **第一条：规范性原则。** 提交信息必须严格遵循 Conventional Commits 规范，包含 type(scope): subject 格式，使用合适的 gitmoji 标识改动类型。
2. **第二条：简洁性原则。** 提交信息应简洁明了，主体内容不超过 50 个字符，必要时可添加详细描述。
3. **第三条：准确性原则。** 提交信息应准确描述变更内容，反映实际的代码改动。
4. **第四条：一致性原则。** 提交信息应与项目中其他提交保持一致的风格和格式。

## 输出格式

请生成符合以下格式的提交信息：

- **提交标题：** 以 gitmoji 开头，后跟符合 Conventional Commits 规范的标题
- **提交主体：**（可选）详细描述变更内容
- **语言：** 默认使用中文来生成提交内容

## Best Practices for Commits

- **Verify before committing**: Ensure code is linted, builds correctly, and documentation is updated
- **Conventional commit format**: Use the format `<type>: <description>` where type is one of:
  - feat: A new feature
  - fix: A bug fix
  - docs: Documentation changes
  - style: Code style changes (formatting, etc)
  - refactor: Code changes that neither fix bugs nor add features
  - perf: Performance improvements
  - test: Adding or fixing tests
  - chore: Changes to the build process, tools, etc.
- **Present tense, imperative mood**: Write commit messages as commands (e.g., "add feature" not "added feature")
- **Concise first line**: Keep the first line under 72 characters
- **Emoji**: Each commit type is paired with an appropriate emoji:
  - ✨ feat: New feature
  - 🐛 fix: Bug fix
  - 📝 docs: Documentation
  - 💄 style: Formatting/style
  - ♻️ refactor: Code refactoring
  - ⚡️ perf: Performance improvements
  - ✅ test: Tests
  - 🔧 chore: Tooling, configuration
  - 🚀 ci: CI/CD improvements
  - 🗑️ revert: Reverting changes
  - 🧪 test: Add a failing test
  - 🚨 fix: Fix compiler/linter warnings
  - 🔒️ fix: Fix security issues
  - 👥 chore: Add or update contributors
  - 🚚 refactor: Move or rename resources
  - 🏗️ refactor: Make architectural changes
  - 🔀 chore: Merge branches
  - 📦️ chore: Add or update compiled files or packages
  - ➕ chore: Add a dependency
  - ➖ chore: Remove a dependency
  - 🌱 chore: Add or update seed files
  - 🧑‍💻 chore: Improve developer experience
  - 🧵 feat: Add or update code related to multithreading or concurrency
  - 🔍️ feat: Improve SEO
  - 🏷️ feat: Add or update types
  - 💬 feat: Add or update text and literals
  - 🌐 feat: Internationalization and localization
  - 👔 feat: Add or update business logic
  - 📱 feat: Work on responsive design
  - 🚸 feat: Improve user experience / usability
  - 🩹 fix: Simple fix for a non-critical issue
  - 🥅 fix: Catch errors
  - 👽️ fix: Update code due to external API changes
  - 🔥 fix: Remove code or files
  - 🎨 style: Improve structure/format of the code
  - 🚑️ fix: Critical hotfix
  - 🎉 chore: Begin a project
  - 🔖 chore: Release/Version tags
  - 🚧 wip: Work in progress
  - 💚 fix: Fix CI build
  - 📌 chore: Pin dependencies to specific versions
  - 👷 ci: Add or update CI build system
  - 📈 feat: Add or update analytics or tracking code
  - ✏️ fix: Fix typos
  - ⏪️ revert: Revert changes
  - 📄 chore: Add or update license
  - 💥 feat: Introduce breaking changes
  - 🍱 assets: Add or update assets
  - ♿️ feat: Improve accessibility
  - 💡 docs: Add or update comments in source code
  - 🗃️ db: Perform database related changes
  - 🔊 feat: Add or update logs
  - 🔇 fix: Remove logs
  - 🤡 test: Mock things
  - 🥚 feat: Add or update an easter egg
  - 🙈 chore: Add or update .gitignore file
  - 📸 test: Add or update snapshots
  - ⚗️ experiment: Perform experiments
  - 🚩 feat: Add, update, or remove feature flags
  - 💫 ui: Add or update animations and transitions
  - ⚰️ refactor: Remove dead code
  - 🦺 feat: Add or update code related to validation
  - ✈️ feat: Improve offline support

## Examples

Good commit messages:

- ✨ feat: add user authentication system
- 🐛 fix: resolve memory leak in rendering process
- 📝 docs: update API documentation with new endpoints
- ♻️ refactor: simplify error handling logic in parser
- 🚨 fix: resolve linter warnings in component files
- 🧑‍💻 chore: improve developer tooling setup process
- 👔 feat: implement business logic for transaction validation
- 🩹 fix: address minor styling inconsistency in header
- 🚑️ fix: patch critical security vulnerability in auth flow
- 🎨 style: reorganize component structure for better readability
- 🔥 fix: remove deprecated legacy code
- 🦺 feat: add input validation for user registration form
- 💚 fix: resolve failing CI pipeline tests
- 📈 feat: implement analytics tracking for user engagement
- 🔒️ fix: strengthen authentication password requirements
- ♿️ feat: improve form accessibility for screen readers

## Command Options

- \--no-verify: Skip running the pre-commit checks (lint)
- 强制提交参数的处理（当参数为 "!" 时使用 `--no-verify`）

## Important Notes

- By default, pre-commit checks (pnpm lint) will run to ensure code quality
- If these checks fail, you'll be asked if you want to proceed with the commit anyway or fix the issues first
- If specific files are already staged, the command will only commit those files
- If no files are staged, it will prompt to stage all modified and new files
- The commit message will be constructed based on the changes detected
- Before committing, the command will review the diff to identify if multiple commits would be more appropriate
- Never modify the files in the committed files automatically, prompting first to confirm if needed
- If suggesting multiple commits, it will help you stage and commit the changes separately
- Always reviews the commit diff to ensure the message matches the changes
- Use Chinese language to generate message by default
