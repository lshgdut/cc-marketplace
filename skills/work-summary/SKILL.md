---
name: work-summary
allowed-tools: Read, Bash(git log *), Bash(git config *), Bash(git rev-parse *), Bash(python3 *), Grep, Glob
description: Generate a concise, human-readable daily or periodic work report. Supports two scopes: the current local repo (via git log) and the whole GitLab instance (via the gitlab-work-report skill). Triggers on requests for a daily/weekly summary, standup notes, or "what did I do" reports.
---

# Work Summary

Generate a polished, human-readable work report for a given period. This skill is the **content/presentation layer**: it picks the right data source, then writes a concise narrative report.

Data fetching is delegated:
- **Local repo** → `git log` on the current project
- **Whole GitLab** → `gitlab-work-report` skill's `fetch_gitlab_activity.py`

## When to use

Use this skill when the user asks for a periodic work summary that reads naturally as a human-written daily / weekly report.

Do NOT use this skill for:
- Raw, structured event dumps (use `gitlab-work-report` for that — it returns the detailed categorized Markdown)
- A single MR / issue description
- Future planning or task tracking
- Team-wide rollups

## Inputs

From the user (ask if any are missing):
1. **Time range** — default `today`; supports: `today`, `yesterday`, `this-week`, `last-week`, `last-7-days`, or explicit `--after/--before`
2. **Scope** — default `current-project`; supports `current-project` (local repo) or `gitlab` (whole instance)
3. **GitLab user** — only required for `gitlab` scope

Infer scope from context when the user is ambiguous:
- "今天的提交" / "这个项目" / no qualifier → `current-project`
- "整个 GitLab" / "GitLab 上的活动" / "我在 GitLab 上的工作" → `gitlab`
- Otherwise ask before fetching

## Workflow

### Step 1: Resolve scope and time range

Determine `(scope, range)` from the user's request. If the user gave a named range, map it to ISO dates (today, yesterday, this-week, etc.). If ambiguous, ask.

For `current-project` scope, also resolve the local author:
```bash
git config user.email   # or user.name as fallback
```

### Step 2: Fetch raw data

**For `current-project`:**
```bash
git log \
  --since="<after> 00:00" \
  --until="<before> 23:59:59" \
  --author="<email or name>" \
  --pretty=format:"%h%x09%s%x09%ad" \
  --date=short \
  --no-merges
```

**For `gitlab`:** delegate to `gitlab-work-report`:
```bash
python3 ../gitlab-work-report/scripts/fetch_gitlab_activity.py \
  --user <username> \
  --range <keyword> \
  --output /tmp/gitlab-events.json
```
Then `Read` the JSON file. The skill `gitlab-work-report` is the canonical source for GitLab API mechanics — see its `SKILL.md` and `references/event-api.md` if you need to adjust query parameters or interpret unusual response shapes.

### Step 3: Write the report

Apply these rules (this is the value-add of this skill — the "content generation"):

1. **Headline + one-line highlights** — first line is a one-sentence summary of the period's main outcome (e.g. "Shipped OAuth support, merged 2 MRs, reviewed 1.").
2. **Group by project** (GitLab scope) or by day (multi-day ranges).
3. **Concise items** — each work item ≤ 20 Chinese characters / ≤ 80 English chars. Shorten commit messages and MR titles; drop prefixes like `feat:`, `fix:`, `WIP:`.
4. **Action verbs** — start each item with a verb: 修复/添加/重构/Review/Merged/Closed/Opened.
5. **Link MRs and issues** — keep the `!iid` / `#iid` reference so the report stays clickable.
6. **Honor filters** — if the user said "只统计 MR" or "don't show commits", drop the rest before writing.

### Output template

```markdown
# <date or range> 工作日报

**今日要点**: <one-sentence summary>

## <project path or "local repo">
- <verb> <subject> [!iid / #iid]
- <verb> <subject>

## <next project>
- ...
```

If there is no activity, write: `_该时间区间内未发现活动。_`

### Step 4: Present and offer next steps

Print the Markdown to the conversation. Then offer:
- Save to a file (default `<cwd>/work-report-<date>.md`)
- Adjust scope, range, or filters
- Translate to English
- Tighten items that exceed the 20-char limit

## Examples

**User: "生成今天的工作报告"**
→ scope=`current-project`, range=`today`. Run `git log` for today, format as a one-day report.

**User: "总结本周 GitLab 上的活动"**
→ scope=`gitlab`, range=`this-week`. Invoke `gitlab-work-report`, then format per the rules above.

**User: "上周的周报"**
→ scope=`current-project`, range=`last-week`. Run `git log` for last Mon–Sun.

**User: "昨天我在 GitLab 上做了什么"**
→ scope=`gitlab`, range=`yesterday`. Invoke `gitlab-work-report` with `--range yesterday`.

**User: "只要 MR，不要 commit"**
→ After fetching, filter out `push` and `issue` events before formatting.

## Notes

- This skill is script-less on purpose: all the "data plumbing" lives in `gitlab-work-report` and `git`, and all the "writing" is the formatting rules in Step 3. Adding scripts here would duplicate the data layer without adding value.
- If `gitlab-work-report` is missing or its scripts have moved, fall back to running its `fetch_gitlab_activity.py` directly with the absolute path the user provides.