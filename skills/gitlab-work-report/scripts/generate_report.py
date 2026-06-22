#!/usr/bin/env python3
"""
Generate a Markdown work report from GitLab activity JSON.

Reads JSON produced by fetch_gitlab_activity.py and writes a Markdown report
with:
  - Executive summary (counts by category, top projects)
  - Detailed sections per category and project

Usage:
  generate_report.py <input.json> [--output report.md]
  fetch_gitlab_activity.py ... | generate_report.py -

Output sections (when present):
  ## 📊 概览
  ## 🏆 主要成果
  ## 🚀 Push / Commits
  ## 🔀 Merge Requests
  ## 📋 Issues
  ## 💬 Comments & Reviews
  ## 📦 其他
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


EMOJI = {
    "push": "🚀",
    "merge_request": "🔀",
    "issue": "📋",
    "comment": "💬",
    "wiki": "📚",
    "milestone": "🏁",
    "other": "📦",
}

SECTION_ORDER = ["push", "merge_request", "issue", "comment", "wiki", "milestone", "other"]
SECTION_TITLE = {
    "push": "Push / Commits",
    "merge_request": "Merge Requests",
    "issue": "Issues",
    "comment": "Comments & Reviews",
    "wiki": "Wiki",
    "milestone": "Milestones",
    "other": "其他活动",
}


# ---------- Categorize & extract (mirror of fetch script) ----------

PUSH_ACTIONS = {"pushed to", "pushed new", "pushed to delete"}


def categorize(event: dict) -> str:
    t = event.get("target_type") or ""
    a = event.get("action_name") or ""
    if t == "Push" or a in PUSH_ACTIONS:
        return "push"
    if t == "MergeRequest":
        return "merge_request"
    if t == "Issue":
        return "issue"
    if t in ("Note", "DiscussionNote", "DiffNote"):
        return "comment"
    if t in ("WikiPage::Meta", "WikiPage"):
        return "wiki"
    if t == "Milestone":
        return "milestone"
    return "other"


def project_path(event: dict) -> str:
    proj = event.get("project") or {}
    return proj.get("path_with_namespace") or f"id:{event.get('project_id')}"


def target_url(event: dict) -> str:
    url = event.get("url") or event.get("target_url") or ""
    if url and not url.startswith("http"):
        # GitLab may return relative paths in some endpoints
        return url
    return url


def push_summary(event: dict) -> str:
    """Build a one-line summary of a push event."""
    pd = event.get("push_data") or {}
    count = pd.get("commit_count") or 0
    ref = pd.get("ref") or ""
    branch = ref.split("/")[-1] if ref.startswith("refs/heads/") else ref
    title = event.get("push_data", {}).get("commit_title") or ""
    if branch and title:
        return f"`{branch}`: {title}" + (f" (+{count - 1} more)" if count > 1 else "")
    if branch:
        return f"`{branch}` ({count} commits)"
    return f"{count} commits"


def mr_summary(event: dict) -> str:
    title = event.get("target_title") or "(no title)"
    iid = event.get("target_iid")
    action = event.get("action_name")
    proj = project_path(event)
    url = target_url(event)
    line = f"**{action}** MR !{iid}: {title}" if iid else f"**{action}** {title}"
    line += f" — _{proj}_"
    if url:
        line += f" [link]({url})"
    return line


def issue_summary(event: dict) -> str:
    title = event.get("target_title") or "(no title)"
    iid = event.get("target_iid")
    action = event.get("action_name")
    proj = project_path(event)
    url = target_url(event)
    line = f"**{action}** Issue #{iid}: {title}" if iid else f"**{action}** {title}"
    line += f" — _{proj}_"
    if url:
        line += f" [link]({url})"
    return line


def comment_summary(event: dict) -> str:
    note = event.get("note") or {}
    noteable = note.get("noteable_type") or "Note"
    iid = note.get("noteable_iid")
    title = event.get("target_title") or ""
    proj = project_path(event)
    url = target_url(event)
    line = f"commented on {noteable}"
    if iid:
        line += f" #{iid}"
    if title:
        line += f": {title}"
    line += f" — _{proj}_"
    if url:
        line += f" [link]({url})"
    return line


def generic_summary(event: dict) -> str:
    title = event.get("target_title") or ""
    action = event.get("action_name") or "activity"
    proj = project_path(event)
    url = target_url(event)
    line = f"**{action}** {title} — _{proj}_"
    if url:
        line += f" [link]({url})"
    return line


# ---------- Aggregations ----------

def build_report(payload: dict) -> str:
    user = payload.get("user") or {}
    rng = payload.get("range") or {}
    events = payload.get("events") or []
    host = payload.get("host", "").rstrip("/")

    by_cat: dict[str, list] = defaultdict(list)
    by_project: dict[str, int] = Counter()
    for e in events:
        cat = categorize(e)
        by_cat[cat].append(e)
        by_project[project_path(e)] += 1

    user_label = user.get("name") or user.get("username") or "user"
    after, before = rng.get("after", "?"), rng.get("before", "?")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# 📅 工作报告：{user_label}")
    lines.append("")
    lines.append(f"- **时间区间**: {after} → {before}")
    lines.append(f"- **GitLab**: {host}")
    lines.append(f"- **生成时间**: {today} UTC")
    lines.append(f"- **事件总数**: {len(events)}")
    lines.append("")

    # Executive summary
    lines.append("## 📊 概览")
    lines.append("")
    lines.append("| 活动类型 | 数量 |")
    lines.append("| --- | ---: |")
    for cat in SECTION_ORDER:
        if by_cat.get(cat):
            lines.append(f"| {EMOJI[cat]} {SECTION_TITLE[cat]} | {len(by_cat[cat])} |")
    lines.append("")

    if by_project:
        lines.append("**涉及项目 (Top 5)**")
        lines.append("")
        for proj, n in by_project.most_common(5):
            lines.append(f"- `{proj}` — {n} events")
        lines.append("")

    # Highlights: merged MRs, closed issues
    highlights = []
    for e in events:
        if e.get("action_name") == "merged" and e.get("target_type") == "MergeRequest":
            highlights.append(f"✅ Merged MR !{e.get('target_iid')}: {e.get('target_title')} — _{project_path(e)}_")
        elif e.get("action_name") == "closed" and e.get("target_type") == "Issue":
            highlights.append(f"✅ Closed issue #{e.get('target_iid')}: {e.get('target_title')} — _{project_path(e)}_")
    if highlights:
        lines.append("## 🏆 主要成果")
        lines.append("")
        for h in highlights:
            lines.append(f"- {h}")
        lines.append("")

    # Detailed sections
    for cat in SECTION_ORDER:
        items = by_cat.get(cat)
        if not items:
            continue
        lines.append(f"## {EMOJI[cat]} {SECTION_TITLE[cat]}")
        lines.append("")

        if cat == "push":
            grouped: dict[str, list] = defaultdict(list)
            for e in items:
                grouped[project_path(e)].append(e)
            for proj, evs in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
                lines.append(f"### `{proj}`")
                lines.append("")
                for e in evs:
                    lines.append(f"- {push_summary(e)}")
                lines.append("")
        elif cat == "merge_request":
            for e in items:
                lines.append(f"- {mr_summary(e)}")
            lines.append("")
        elif cat == "issue":
            for e in items:
                lines.append(f"- {issue_summary(e)}")
            lines.append("")
        elif cat == "comment":
            for e in items:
                lines.append(f"- {comment_summary(e)}")
            lines.append("")
        else:
            for e in items:
                lines.append(f"- {generic_summary(e)}")
            lines.append("")

    if not events:
        lines.append("_该时间区间内未发现活动。_")
        lines.append("")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Generate Markdown work report from GitLab activity JSON.")
    p.add_argument("input", help="Path to JSON file, or '-' for stdin")
    p.add_argument("--output", "-o", help="Output path (default: stdout)")
    args = p.parse_args()

    if args.input == "-":
        payload = json.load(sys.stdin)
    else:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))

    report = build_report(payload)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
