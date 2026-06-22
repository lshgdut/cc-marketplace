---
name: glab-merge-request
description: Create and submit a GitLab Merge Request workflow. 
disable-model-invocation: false
allowed-tools:
  - Bash(git status *)
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git branch *)
  - Bash(git checkout *)
  - Bash(git remote *)
  - Bash(git config *)
  - Bash(git log *)
  - Bash(glab *)
  - Bash(which glab)
  - Bash(openssl rand *)
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# GitLab Merge Request Workflow

This workflow automatically:

1. Creates a safe working branch when needed
2. Commits local changes
3. Pushes the current branch to GitLab
4. Creates or updates a GitLab Merge Request

The workflow follows an **execute-first** strategy:

* Prefer directly executing the workflow
* Only provide dependency setup guidance when a command actually fails
* Minimize unnecessary pre-checks and interruptions

---

## When to use

Use when the user wants to:

* push the current branch
* create a GitLab Merge Request
* quickly submit current work to GitLab

Examples:

* `/mr`
* `create mr`
* `help me to create gitLab mr`

---

## Execution Strategy

The workflow should:

* attempt the operation directly
* infer repository state dynamically
* recover from common git/glab failures automatically when possible
* only ask the user for intervention when recovery is impossible

Do NOT perform blocking prerequisite checks before execution.

Examples of checks that should be deferred until failure:

* `glab` installation
* GitLab authentication
* remote repository existence

---

## Step 1: Determine Working Branch

Get current branch:

```bash
git branch --show-current
```

If current branch is:

* `main`
* `master`
* `develop`
* `dev`
* matches `dev-*`
* detached HEAD
* empty branch name

Then create a personal feature branch automatically.

Example:

```bash
git checkout -b "mr-$(git config user.name | tr ' ' '-')-$(openssl rand -hex 3)"
```

Otherwise continue using current branch.

---

## Step 2: Handle Local Changes

Check repository status:

```bash
git status --short
```

### No Changes

If working tree is clean:

```text
No local changes detected.
Skipping commit step.
```

Continue directly to MR creation.

---

### Existing Staged Changes

If staged changes already exist:

```bash
git diff --cached --stat
```

Then:

* do NOT run `git add .`
* commit staged content only

---

### Unstaged Changes

Stage files carefully:

```bash
git add --update
git add <new-files-if-needed>
```

Avoid:

```bash
git add .
```

to reduce accidental commits of generated files, secrets, logs, or build artifacts.

---

## Step 3: Create Commit

Create commit using conventional commit style.

Recommended formats:

```text
feat: add xxx
fix: resolve xxx
refactor: improve xxx
docs: update xxx
chore: cleanup xxx
```

If commit fails:

* show git error output
* ask whether to continue MR creation without committing

---

## Step 4: Push and Create Merge Request

### 4.1: Determine Target Branch

```bash
git remote show origin | grep 'HEAD branch'
```

If detected, use it as `--target-branch`. Otherwise fall back to `main`.

### 4.2: Generate MR Title and Description

Generate the title and description from **all commits in the MR**, not just the latest. If a GitLab MR template exists, use it as the structure for the description.

**Collect commits between source and target:**

```bash
git log <target-branch>..<source-branch> --pretty=format:"%s%n%n%b%n---%n"
```

**Check for a GitLab MR template** (in priority order):

1. `.gitlab/merge_request.md` — single file
2. `.gitlab/merge_request_templates/<name>.md` — named template

Use `Glob` to locate templates, `Read` to load content.

**Build content:**

* **Title**: aggregate commit subjects into a single conventional title (e.g. `feat+fix: add login and resolve timeout`)
* **Description**:
  * If a template exists, preserve its sections and fill its placeholders from the commit content
  * Otherwise, summarize the commits: what changed, why, and how to verify

### 4.3: Create MR

Pass the generated content explicitly. Do **not** use `--fill`:

```bash
glab mr create \
  --title "$MR_TITLE" \
  --description "$MR_DESCRIPTION" \
  --target-branch <default-branch> \
  --push \
  --yes \
  --remove-source-branch \
  --create-source-branch \
  --no-editor
```

---

## Failure Recovery

Only provide setup instructions after a related command fails.

### glab not installed

If `glab` command is missing:

```text
GitLab CLI (glab) is not installed.

Install with:

  brew install glab

Documentation:
https://gitlab.com/gitlab-org/cli/-/blob/main/docs/installation_options.md
```

Stop execution.

---

### GitLab authentication failed

If GitLab authentication is missing or expired:

```text
Please login to GitLab first:

  glab auth login

For self-hosted GitLab:

  glab auth login --hostname <gitlab.example.org>
```

Stop execution.

---

### No remote repository

If git remote is missing:

```text
No git remote repository is configured.

Example:

  git remote add origin <repository-url>
```

Stop execution.

---

### Push rejected

If push is rejected:

* show remote rejection reason
* suggest pull/rebase if appropriate

---

### MR already exists

If an MR already exists for the branch:

* update existing MR when possible
* otherwise return existing MR link

---

## Optional Enhancements

### Draft MR support

```bash
glab mr create --draft
```

---

### Conventional commit validation

```bash
git log -1 --pretty=%s
```

Validate commit format before MR creation.

---

## Expected Outcome

After successful execution:

* local changes are committed
* branch is pushed to GitLab
* Merge Request is created or updated
* source branch is configured for automatic cleanup after merge
