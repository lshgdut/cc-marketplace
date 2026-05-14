---
name: glab-mr
description: Create and submit a GitLab Merge Request workflow. 
disable-model-invocation: true

allowed-tools:
  - Bash(git status *)
  - Bash(git diff *)
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git branch *)
  - Bash(git checkout *)
  - Bash(git rev-parse *)
  - Bash(git remote *)
  - Bash(git config *)
  - Bash(glab *)
  - Bash(which glab)
  - Bash(openssl rand *)
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# GitLab Merge Request Workflow

This workflow automates the full process of:

1. Validating GitLab CLI availability
2. Ensuring a safe working branch
3. Committing local changes
4. Pushing the branch
5. Creating or updating a GitLab Merge Request

---

## When to use

Use when the user says "/mr", "create MR", "submit merge request", or asks to push the current branch and open a GitLab Merge Request automatically.

## Preconditions

### 1. Verify GitLab CLI installation

```bash
which glab || echo "NOT_INSTALLED"
```

If not installed:

```text
GitLab CLI (glab) is not installed.

Install with:

  brew install glab

Documentation:
https://gitlab.com/gitlab-org/cli/-/blob/main/docs/installation_options.md
```

Stop execution.

---

### 2. Verify GitLab authentication

```bash
glab auth status
```

If authentication fails:

```text
Please login to GitLab first:

  glab auth login

Or for self-hosted GitLab:

  glab auth login --hostname <gitlab.example.org>
```

Stop execution.

---

### 3. Verify git remote exists

```bash
git remote -v
```

If no remote is configured:

```text
No git remote repository is configured.

Please configure a remote first, for example:

  git remote add origin <repository-url>
```

Stop execution.

---

## Step 1: Ensure Safe Working Branch

Get current branch:

```bash
git branch --show-current
```

### Branch Rules

If current branch is:

- `main`
- `master`
- `develop`
- `dev`
- matches `dev-*`
- detached HEAD
- empty branch name

Then automatically create a personal feature branch.

Generate branch name:

```bash
AUTHOR=$(git config user.name | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
RANDOM_SUFFIX=$(openssl rand -hex 3)

BRANCH_NAME="mr-${AUTHOR}-${RANDOM_SUFFIX}"
```

Create and switch branch:

```bash
git checkout -b "$BRANCH_NAME"
```

Otherwise continue using current branch.

---

## Step 2: Commit Local Changes

Check repository status:

```bash
git status --short
```

### Change Handling Rules

#### Case A: No changes

If working tree is clean:

```text
No local changes detected.
Skipping commit step.
```

Continue directly to MR creation.

---

#### Case B: Staged changes already exist

Check staged diff:

```bash
git diff --cached --stat
```

If staged changes exist:

- Do NOT run `git add`
- Commit existing staged changes only

---

#### Case C: Unstaged changes exist

Stage tracked and untracked files carefully:

```bash
git add --update
git add <new-files-if-needed>
```

Avoid blindly using:

```bash
git add .
```

to reduce accidental commits of generated files, secrets, logs, or build artifacts.

---

### Commit Creation

Create commit using project commit conventions.

Recommended format:

```text
feat: add xxx
fix: resolve xxx
refactor: improve xxx
docs: update xxx
chore: cleanup xxx
```

If commit fails:

- Show git error output
- Ask user whether to continue MR creation without committing

---

## Step 3: Push Branch and Create Merge Request

Create or update MR:

```bash
glab mr create \
  --fill \
  --push \
  --yes \
  --target-branch main \
  --remove-source-branch \
  --create-source-branch \
  --no-editor
```

---

## Recommended Optional Enhancements

### Auto-detect default branch

Instead of hardcoding `main`:

```bash
git remote show origin | grep 'HEAD branch'
```

Use detected default branch as MR target.

---

### Support draft MR

If work is incomplete:

```bash
glab mr create --draft
```

---

### Support conventional commit validation

Optional:

```bash
git log -1 --pretty=%s
```

Validate commit message format before MR creation.

---

## Error Handling

| Scenario | Action |
|---|---|
| glab not installed | Show installation instructions and stop |
| glab not authenticated | Show login instructions and stop |
| no git remote | Ask user to configure remote |
| branch creation failed | Stop and show git error |
| commit failed | Show error and ask whether to continue |
| push rejected | Show remote rejection reason |
| MR already exists | Update existing MR if possible |
| no changes detected | Skip commit and create MR directly |

---

## Expected Outcome

After successful execution:

- Local changes are committed
- Branch is pushed to remote
- Merge Request is created or updated
- Source branch is configured for auto-removal after merge
