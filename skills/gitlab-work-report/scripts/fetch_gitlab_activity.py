#!/usr/bin/env python3
"""
Fetch user activity events from GitLab REST API for a given date range.

Outputs JSON to stdout with the following structure:
{
  "user": {"id": ..., "username": ..., "name": ...},
  "range": {"after": "YYYY-MM-DD", "before": "YYYY-MM-DD"},
  "events": [
    {
      "action_name": "pushed to",
      "target_type": "Issue" | "MergeRequest" | "Note" | "Push" | ...,
      "target_title": "...",
      "project_id": ...,
      "project": {"path_with_namespace": "..."},
      "created_at": "ISO8601",
      "push_data": {...},            # for push events
      "note": {"noteable_type": ..., "noteable_iid": ...},  # for comments
      "url": "..."
    }
  ]
}

Environment:
  GITLAB_HOST   - GitLab base URL (default: https://gitlab.com)
  GITLAB_TOKEN  - Personal access token (required for non-/users/:id/events feed)

Examples:
  fetch_gitlab_activity.py --user wenhua --after 2026-06-15 --before 2026-06-22
  fetch_gitlab_activity.py --user wenhua --range last-week
  fetch_gitlab_activity.py --user wenhua --range this-month --output events.json
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from typing import Optional


DEFAULT_HOST = "https://gitlab.com"
PER_PAGE = 100
MAX_PAGES = 50


# ---------- Date helpers ----------

def resolve_range(after, before, range_key):
    """Resolve (after, before) from explicit values or a named range."""
    if range_key:
        today = date.today()
        if range_key == "today":
            return today.isoformat(), today.isoformat()
        if range_key == "yesterday":
            y = today - timedelta(days=1)
            return y.isoformat(), y.isoformat()
        if range_key == "this-week":
            monday = today - timedelta(days=today.weekday())
            return monday.isoformat(), today.isoformat()
        if range_key == "last-week":
            this_monday = today - timedelta(days=today.weekday())
            last_monday = this_monday - timedelta(days=7)
            last_sunday = this_monday - timedelta(days=1)
            return last_monday.isoformat(), last_sunday.isoformat()
        if range_key == "this-month":
            return today.replace(day=1).isoformat(), today.isoformat()
        if range_key == "last-month":
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start.isoformat(), last_month_end.isoformat()
        if range_key == "last-7-days":
            return (today - timedelta(days=7)).isoformat(), today.isoformat()
        if range_key == "last-30-days":
            return (today - timedelta(days=30)).isoformat(), today.isoformat()
        raise SystemExit(f"Unknown range: {range_key}")
    if not after or not before:
        raise SystemExit("Must provide --after/--before or --range")
    return after, before


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


# ---------- HTTP ----------

def http_get(url, token, params):
    qs = urllib.parse.urlencode(params)
    full = f"{url}?{qs}" if qs else url
    req = urllib.request.Request(full, method="GET")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("PRIVATE-TOKEN", token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        next_link = resp.headers.get("Link", "")
    return json.loads(body), parse_next_link(next_link)


def parse_next_link(header):
    if not header:
        return None
    for part in header.split(","):
        if 'rel="next"' in part:
            url = part.split(";")[0].strip().strip("<>")
            return url
    return None


# ---------- Lookup ----------

def lookup_user_id(host, username, token):
    url = f"{host}/api/v4/users"
    data, _ = http_get(url, token, {"username": username})
    if not data:
        raise SystemExit(f"User not found: {username}")
    return {"id": data[0]["id"], "username": data[0]["username"], "name": data[0]["name"]}


# ---------- Event fetch ----------

def fetch_events(host, user_id, after, before, token):
    """Fetch all events in range with pagination."""
    url = f"{host}/api/v4/users/{user_id}/events"
    params = {"after": after, "before": before, "per_page": PER_PAGE, "sort": "desc"}
    out = []
    pages = 0
    next_url = None
    while True:
        if next_url:
            req = urllib.request.Request(next_url, method="GET")
            req.add_header("Accept", "application/json")
            if token:
                req.add_header("PRIVATE-TOKEN", token)
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                next_link = resp.headers.get("Link", "")
            data = json.loads(body)
            next_url = parse_next_link(next_link)
        else:
            data, next_url = http_get(url, token, params)
        out.extend(data)
        pages += 1
        if not next_url or pages >= MAX_PAGES:
            break
        time.sleep(0.05)
    return out


# ---------- Filtering ----------

PUSH_ACTIONS = {"pushed to", "pushed new", "pushed to delete"}
MR_ACTIONS = {"opened", "closed", "merged", "approved", "created"}
ISSUE_ACTIONS = {"opened", "closed", "created"}
NOTE_ACTIONS = {"commented on", "commented"}
REVIEW_ACTIONS = {"approved"}


def filter_events(events, include):
    """Optionally include only specific event categories."""
    if not include:
        return events
    keep = []
    for e in events:
        cat = categorize(e)
        if cat in include:
            keep.append(e)
    return keep


def categorize(event):
    t = event.get("target_type") or ""
    a = event.get("action_name") or ""
    if t == "Push" or a in PUSH_ACTIONS:
        return "push"
    if t in ("MergeRequest",):
        return "merge_request"
    if t in ("Issue",):
        return "issue"
    if t in ("Note", "DiscussionNote", "DiffNote"):
        return "comment"
    if t in ("WikiPage::Meta", "WikiPage"):
        return "wiki"
    if t in ("Milestone",):
        return "milestone"
    return "other"


# ---------- Main ----------

def main():
    p = argparse.ArgumentParser(description="Fetch GitLab user activity events.")
    p.add_argument("--host", default=os.environ.get("GITLAB_HOST", DEFAULT_HOST))
    p.add_argument("--user", required=True, help="GitLab username")
    p.add_argument("--after", help="Start date (YYYY-MM-DD)")
    p.add_argument("--before", help="End date (YYYY-MM-DD)")
    p.add_argument("--range", choices=[
        "today", "yesterday", "this-week", "last-week",
        "this-month", "last-month", "last-7-days", "last-30-days",
    ])
    p.add_argument("--include", help="Comma-separated event categories: push,merge_request,issue,comment,wiki,milestone")
    p.add_argument("--output", help="Write JSON to file (default: stdout)")
    p.add_argument("--token", default=os.environ.get("GITLAB_TOKEN"))
    args = p.parse_args()

    if not args.token:
        print("Warning: GITLAB_TOKEN not set; /users/:id/events may return empty results.", file=sys.stderr)

    after, before = resolve_range(args.after, args.before, args.range)
    try:
        parse_date(after); parse_date(before)
    except ValueError as e:
        raise SystemExit(f"Invalid date: {e}")

    user = lookup_user_id(args.host, args.user, args.token)
    events = fetch_events(args.host, user["id"], after, before, args.token)

    include = set(args.include.split(",")) if args.include else None
    if include:
        events = filter_events(events, include)

    payload = {
        "user": user,
        "range": {"after": after, "before": before},
        "host": args.host,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "event_count": len(events),
        "events": events,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {len(events)} events to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
