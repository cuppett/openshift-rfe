# RFE JQL Patterns & Field Reference

## Base Query

Every `rfe-browse` search starts from:

```
project = RFE AND issuetype = "Feature Request"
```

Append filter clauses and sort order before executing.

---

## Pre-built JQL Patterns

### Open RFEs (default — all open statuses)

```
project = RFE AND issuetype = "Feature Request"
AND status in ("New", "In Progress", "Under Consideration", "Triaged")
ORDER BY priority ASC, votes DESC, created DESC
```

### High-priority open RFEs

```
project = RFE AND issuetype = "Feature Request"
AND status in ("New", "In Progress", "Under Consideration", "Triaged")
AND priority in (Critical, Major)
ORDER BY priority ASC, votes DESC
```

### Most-voted open RFEs

```
project = RFE AND issuetype = "Feature Request"
AND status in ("New", "In Progress", "Under Consideration", "Triaged")
AND votes > 0
ORDER BY votes DESC, priority ASC
```

### Recent RFEs (created or updated in last 90 days)

```
project = RFE AND issuetype = "Feature Request"
AND (created >= -90d OR updated >= -90d)
ORDER BY updated DESC
```

### By component

```
project = RFE AND issuetype = "Feature Request"
AND component = "<COMPONENT-NAME>"
AND status in ("New", "In Progress", "Under Consideration", "Triaged")
ORDER BY priority ASC, votes DESC
```

Replace `<COMPONENT-NAME>` with values like `ROSA`, `HyperShift`, `XCMSTRAT`, `MCE`, etc.

### By label

```
project = RFE AND issuetype = "Feature Request"
AND labels = "<LABEL>"
ORDER BY priority ASC, votes DESC
```

### Text search (summary and description)

```
project = RFE AND issuetype = "Feature Request"
AND text ~ "<KEYWORDS>"
ORDER BY priority ASC, votes DESC, created DESC
```

Use double quotes for multi-word phrases: `text ~ "managed cluster"`.

### Combined: high-priority + component + open

```
project = RFE AND issuetype = "Feature Request"
AND component = "<COMPONENT>"
AND priority in (Critical, Major)
AND status in ("New", "In Progress", "Under Consideration", "Triaged")
ORDER BY votes DESC, created DESC
```

---

## Field Reference

| API field name | Description | Notes |
|----------------|-------------|-------|
| `summary` | Issue title / one-liner | Always present |
| `status` | Workflow state | Name values: `New`, `In Progress`, `Under Consideration`, `Triaged`, `Closed`, `Won't Fix` |
| `priority` | Priority level | Values: `Critical`, `Major`, `Minor`, `Undefined` |
| `components` | Product components | Array of `{name}` objects |
| `labels` | Free-form tags | Array of strings |
| `votes` | Vote object | `votes.votes` = count; `votes.hasVoted` = current user |
| `created` | ISO-8601 creation timestamp | Slice `[:10]` for YYYY-MM-DD |
| `updated` | ISO-8601 last-updated timestamp | |
| `issuelinks` | Linked issue array | Each entry has `type.inward`, `type.outward`, `inwardIssue`, `outwardIssue` |
| `description` | Full body text (wiki markup) | May be `null`; truncate for display |

---

## The `unlinked` Filter — Why It's Post-processing

JQL has no operator to query "issues that have no linked issue of type Feature". The closest approximation (`issueFunction` in Jira's ScriptRunner) is not universally available.

**The correct approach:**

1. Run the JQL search requesting the `issuelinks` field.
2. For each result, inspect `issuelinks` and check whether any linked issue has `issuetype.name == "Feature"`.
3. Discard results that have one or more such links.

This means the `maxResults` parameter applies **before** the post-filter. If you request 25 results and 20 have Features linked, you'll only display 5. When `unlinked` is active, increase `maxResults` (e.g., to 100) to improve yield.

---

## REST API Search Endpoint

```
GET https://issues.redhat.com/rest/api/2/search
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `jql` | string | URL-encoded JQL query |
| `maxResults` | int | Max issues to return (default 50, cap 100) |
| `startAt` | int | Pagination offset (default 0) |
| `fields` | comma-list | Fields to return; controls response size |

**Recommended `fields` value for rfe-browse:**

```
summary,status,priority,components,labels,votes,created,updated,issuelinks,description
```

**Authentication:** Bearer token from `$JIRA_API_TOKEN`.

```python
import os, requests

token = os.environ['JIRA_API_TOKEN']
resp = requests.get(
    'https://issues.redhat.com/rest/api/2/search',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    },
    params={
        'jql': jql,
        'maxResults': 50,
        'fields': 'summary,status,priority,components,labels,votes,created,updated,issuelinks,description'
    }
)
data = resp.json()
# data['total']  — total matching issues
# data['issues'] — list of issue objects
```

**Response structure per issue:**

```json
{
  "key": "RFE-1234",
  "fields": {
    "summary": "...",
    "status": {"name": "New"},
    "priority": {"name": "Critical"},
    "components": [{"name": "ROSA"}],
    "labels": ["cloud-experience"],
    "votes": {"votes": 12, "hasVoted": false},
    "created": "2024-11-01T10:00:00.000+0000",
    "updated": "2025-01-15T14:30:00.000+0000",
    "issuelinks": [
      {
        "type": {"inward": "is implemented by", "outward": "implements"},
        "outwardIssue": {
          "key": "ROSA-456",
          "fields": {
            "summary": "...",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Feature"}
          }
        }
      }
    ],
    "description": "..."
  }
}
```
