# GitLab Events API Reference

Reference for the `GET /users/:id/events` endpoint used by `fetch_gitlab_activity.py`.

## Endpoint

```
GET /api/v4/users/:id/events
```

Authentication: `PRIVATE-TOKEN` header. A token is required to see events from private groups / projects the user is a member of. Public events on public projects may be visible without a token.

## Query parameters

| Param      | Type   | Notes                                                                       |
| ---------- | ------ | --------------------------------------------------------------------------- |
| `after`    | date   | `YYYY-MM-DD`. Inclusive lower bound on `created_at`, interpreted in **UTC**. |
| `before`   | date   | `YYYY-MM-DD`. Inclusive upper bound on `created_at`, interpreted in **UTC**. |
| `per_page` | int    | Up to 100; the fetch script uses 100.                                       |
| `page`     | int    | 1-based. The fetch script auto-paginates via the `Link: rel="next"` header. |
| `sort`     | string | `asc` or `desc` on `created_at`. Script defaults to `desc`.                 |

## Event shape

Common fields used by the report builder:

```json
{
  "action_name": "pushed to",        // see table below
  "target_type": "Push",             // see table below
  "target_id": 12345,
  "target_iid": 7,                   // human-friendly id (MR/issue number)
  "target_title": "Fix login bug",
  "project_id": 42,
  "project": { "path_with_namespace": "group/repo" },
  "author": { "id": 1, "username": "alice", "name": "Alice" },
  "created_at": "2026-06-15T08:30:00.000Z",
  "push_data": {                     // only for target_type=Push
    "commit_count": 3,
    "ref": "refs/heads/main",
    "commit_title": "Fix login bug"
  },
  "note": {                          // only for target_type=Note
    "noteable_type": "MergeRequest",
    "noteable_iid": 7
  },
  "url": "https://gitlab.com/group/repo/-/merge_requests/7"
}
```

## `action_name` values

The values that matter for this report:

| action_name        | target_type         | Reported as |
| ------------------ | ------------------- | ----------- |
| `pushed to`        | `Push`              | push        |
| `pushed new`       | `Push`              | push        |
| `pushed to delete` | `Push`              | push        |
| `opened`           | `MergeRequest`      | merge_request |
| `closed`           | `MergeRequest`      | merge_request |
| `merged`           | `MergeRequest`      | merge_request |
| `approved`         | `MergeRequest`      | merge_request |
| `opened`           | `Issue`             | issue       |
| `closed`           | `Issue`             | issue       |
| `commented on`     | `Note` / `DiffNote` | comment     |
| `created`          | `WikiPage` etc.     | wiki        |

## Pagination

GitLab returns up to `per_page` events and signals more via:

```
Link: <https://gitlab.com/api/v4/users/1/events?page=2&per_page=100>; rel="next",
      <https://gitlab.com/api/v4/users/1/events?page=10&per_page=100>; rel="last"
```

The fetch script parses the `rel="next"` link and follows it until exhausted or 50 pages (5,000 events) is reached.

## Rate limits

GitLab.com: 2,000 requests/min per user for authenticated requests. The fetch script does 1 request per 100 events, so 5,000 events = 50 requests — well under the limit. Self-hosted admins may set stricter limits; back off if you see HTTP 429.

## Self-hosted notes

- API path is always `/api/v4/...` regardless of host.
- Older self-hosted instances (pre-12.0) may return slightly different `target_type` values for some actions.
- Some self-hosted instances disable the `events` endpoint entirely for non-admins; in that case, fall back to scraping per-project events or MR/issue lists with the `glab` CLI.