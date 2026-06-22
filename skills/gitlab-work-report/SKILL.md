---
name: gitlab-work-report
description: Generate a Markdown work report from a GitLab user's activity events for a specified date range. Triggers on requests for weekly/monthly summaries, standup notes, or "what did I do on GitLab" reports.
allowed-tools: Bash, Read
---

# GitLab Work Report

汇总指定时间区间内 GitLab 用户的活动事件，输出可粘贴到周报/月报/绩效文档的 Markdown 报告。

## When to use

Use this skill when the user asks for a work report / activity summary based on GitLab events for a specific time period. Common triggers:
- "总结一下这周的工作" / "上周的周报" / "本月工作报告"
- "GitLab 上我最近做了什么" / "我的 MR 列表"
- "Generate my work summary" / "weekly standup notes"
- "统计我最近30天在 GitLab 上的活动"

Do NOT use this skill for:
- Local-only git history summaries (use the `work-summary` skill for that)
- Single MR/issue descriptions or code review
- Team-wide reports (this skill scopes to a single user)

## Inputs

Required (from user, in order of preference):
1. **Time range keyword** — `today`, `yesterday`, `this-week`, `last-week`, `this-month`, `last-month`, `last-7-days`, `last-30-days` (default: `last-7-days` if none given)
2. **Or explicit dates** — `--after YYYY-MM-DD --before YYYY-MM-DD`
3. **Optional filters** — "只统计 MR", "不要 issue", "只看评论" → maps to `--include merge_request,comment` etc.
4. **GitLab user** — username; if omitted, ask

Environment:
- `GITLAB_HOST` — base URL (default `https://gitlab.com`)
- `GITLAB_TOKEN` — personal access token; required for non-public events. If unset, warn and try anyway.

## Workflow

1. **Resolve the time range.** Convert the user's keyword to ISO dates using `scripts/fetch_gitlab_activity.py`'s `--range` flag, or parse explicit dates. If ambiguous, ask the user to choose.
2. **Fetch events** by running:
   ```bash
   python3 scripts/fetch_gitlab_activity.py \
     --user <username> \
     [--range <keyword> | --after YYYY-MM-DD --before YYYY-MM-DD] \
     [--include push,merge_request,issue,comment] \
     --output /tmp/gitlab-events.json
   ```
   - If `GITLAB_TOKEN` is not set in the environment, prompt the user or pass `--token`.
   - If the user provided a self-hosted GitLab, pass `--host https://gitlab.example.com` or set `GITLAB_HOST`.
3. **Generate the report** by piping the JSON into the report builder:
   ```bash
   python3 scripts/generate_report.py /tmp/gitlab-events.json --output /tmp/work-report.md
   ```
   Or in one step:
   ```bash
   python3 scripts/fetch_gitlab_activity.py --user <u> --range last-week \
     | python3 scripts/generate_report.py -
   ```
4. **Show the report to the user.** Print the Markdown to the conversation. Offer to:
   - Save to a file
   - Filter to a specific category
   - Adjust the date range
   - Translate to English / add more detail

## Output format

The report is Markdown with these sections (only present when relevant):

- `# 📅 工作报告：<name>` — header with range and total event count
- `## 📊 概览` — counts by category + top 5 projects
- `## 🏆 主要成果` — auto-highlighted merged MRs and closed issues
- `## 🚀 Push / Commits` — grouped by project, branch + commit title
- `## 🔀 Merge Requests` — action + !iid + title + project + link
- `## 📋 Issues` — same shape as MRs
- `## 💬 Comments & Reviews` — noteable type + iid + title
- `## 📦 其他` — wiki, milestone, and uncategorized events

## Scripts

- `scripts/fetch_gitlab_activity.py` — paginates `/api/v4/users/:id/events?after=&before=` and emits JSON
- `scripts/generate_report.py` — formats the JSON into Markdown

Both scripts run with only the Python 3 standard library (no pip install needed).

## Resources

### references/
- `event-api.md` — GitLab Events API reference: action_name values, target_type values, query params, pagination.

## Common pitfalls

- **Timezone**: GitLab's `after`/`before` are interpreted in UTC. Confirm with the user if their local week boundary matters (e.g. "this week" could mean Mon-Sun in their TZ).
- **Self-hosted GitLab**: API path is always `/api/v4/...` regardless of host.
- **Token scopes**: read `api` is safest; a token with `read_user` + membership in target groups is often enough for self-events.
- **Empty results**: an empty events list usually means wrong host, expired token, or the user has no public activity in that range.
- **Pagination**: the fetch script caps at 50 pages × 100 events = 5,000 events per range, which is well above any realistic single-user weekly volume.
