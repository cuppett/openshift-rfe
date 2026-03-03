#!/usr/bin/env python3
"""Search JIRA for RFEs and classify each by Feature coverage.

Usage:
    uv run --with requests python3 rfe-search.py --jql "..." [--limit N]

Environment:
    JIRA_API_TOKEN  Personal Access Token for issues.redhat.com

Output:
    Line 1: summary header  "Total matches: N (showing M)"
    Lines 2+: one JSON object per issue, fields:
        key, summary, status, priority, votes, components,
        updated, feature_links, coverage
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

    resp = requests.get(
        "https://issues.redhat.com/rest/api/2/search",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        params={
            "jql": args.jql,
            "maxResults": args.limit,
            "fields": "summary,status,priority,components,labels,votes,created,updated,issuelinks",
        },
    )

    if not resp.ok:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    issues = data["issues"]
    print(f"Total matches: {data['total']} (showing {len(issues)})")
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

        print(
            json.dumps(
                {
                    "key": key,
                    "summary": f.get("summary", ""),
                    "status": status,
                    "priority": (f.get("priority") or {}).get("name", "Unknown"),
                    "votes": (f.get("votes") or {}).get("votes", 0),
                    "components": ", ".join(c["name"] for c in f.get("components", [])),
                    "updated": (f.get("updated") or "")[:10],
                    "feature_links": feature_links,
                    "coverage": coverage,
                }
            )
        )


if __name__ == "__main__":
    main()
