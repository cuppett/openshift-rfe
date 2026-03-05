#!/usr/bin/env python3
"""Search JIRA for RFEs and classify each by Feature coverage.

Usage:
    uv run --with requests python3 rfe-search.py --jql "..." [--limit N] [--all]

Environment:
    JIRA_API_TOKEN  Personal Access Token for issues.redhat.com

Output:
    Line 1: summary header  "Total matches: N (showing M)"
    Lines 2+: one JSON object per issue, fields:
        key, summary, status, priority, votes, components,
        labels, created, updated, description, feature_links, coverage
    coverage values: "none" | "partial" | "decomposed"
"""

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Search JIRA RFEs")
    parser.add_argument("--jql", required=True, help="JQL query string")
    parser.add_argument(
        "--limit", type=int, default=25, help="Max results (default 25)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all results via pagination (ignores --limit)",
    )
    args = parser.parse_args()

    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        print("ERROR: JIRA_API_TOKEN not set", file=sys.stderr)
        print("Set:      export JIRA_API_TOKEN=<your-PAT>", file=sys.stderr)
        print(
            "Generate: https://issues.redhat.com/secure/ViewProfile.jspa",
            file=sys.stderr,
        )
        sys.exit(1)

    import requests

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    fields = "summary,status,priority,components,labels,votes,created,updated,issuelinks,description"

    if args.all:
        # Paginate through all results
        start_at = 0
        total = None
        issues = []

        while True:
            page_size = 100
            if total is not None:
                remaining = total - start_at
                if remaining <= 0:
                    break
                page_size = min(100, remaining)

            resp = requests.get(
                "https://issues.redhat.com/rest/api/2/search",
                headers=headers,
                params={
                    "jql": args.jql,
                    "maxResults": page_size,
                    "startAt": start_at,
                    "fields": fields,
                },
            )

            if not resp.ok:
                print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
                sys.exit(1)

            data = resp.json()
            total = data["total"]
            page_issues = data["issues"]
            issues.extend(page_issues)
            start_at += len(page_issues)

            if start_at >= total or not page_issues:
                break
    else:
        resp = requests.get(
            "https://issues.redhat.com/rest/api/2/search",
            headers=headers,
            params={
                "jql": args.jql,
                "maxResults": args.limit,
                "fields": fields,
            },
        )

        if not resp.ok:
            print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)

        data = resp.json()
        issues = data["issues"]
        total = data["total"]

    print(f"Total matches: {total} (showing {len(issues)})")
    print()

    for issue in issues:
        key = issue["key"]
        f = issue["fields"]
        status = f["status"]["name"]

        feature_links = []
        for link in f.get("issuelinks", []):
            for direction in ("inwardIssue", "outwardIssue"):
                li = link.get(direction)
                if li:
                    ltype = li.get("fields", {}).get("issuetype", {}).get("name", "")
                    if ltype == "Feature":
                        feature_links.append(li["key"])

        coverage = "none"
        if feature_links:
            coverage = (
                "partial"
                if status not in ("Closed", "Done", "Resolved")
                else "decomposed"
            )

        description = (f.get("description") or "")[:500]

        print(
            json.dumps(
                {
                    "key": key,
                    "summary": f.get("summary", ""),
                    "status": status,
                    "priority": (f.get("priority") or {}).get("name", "Unknown"),
                    "votes": (f.get("votes") or {}).get("votes", 0),
                    "components": ", ".join(c["name"] for c in f.get("components", [])),
                    "labels": f.get("labels", []),
                    "created": (f.get("created") or "")[:10],
                    "updated": (f.get("updated") or "")[:10],
                    "description": description,
                    "feature_links": feature_links,
                    "coverage": coverage,
                }
            )
        )


if __name__ == "__main__":
    main()
