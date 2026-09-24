import pandas as pd

from github_client import get_paginated
from utils.dates import to_utc


def safe_login(user):
    if not user:
        return "Unknown"

    return user.get("login") or "Unknown"


def get_issues(
    owner,
    repo,
):
    raw_issues = get_paginated(
        f"/repos/{owner}/{repo}/issues",
        {
            "state": "all",
            "sort": "created",
            "direction": "asc",
        },
    )

    rows = []

    for issue in raw_issues:

        # GitHub's issues endpoint also
        # returns pull requests.
        if "pull_request" in issue:
            continue

        user = issue.get("user") or {}

        rows.append({
            "repo": repo,
            "number": issue.get("number"),
            "title": issue.get(
                "title",
                "",
            ),
            "author": safe_login(user),
            "author_type": user.get("type"),
            "state": issue.get("state"),
            "created_at": issue.get(
                "created_at"
            ),
            "updated_at": issue.get(
                "updated_at"
            ),
            "closed_at": issue.get(
                "closed_at"
            ),
            "comments_count": issue.get(
                "comments",
                0,
            ),
            "html_url": issue.get(
                "html_url"
            ),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["created_at"] = to_utc(
            df["created_at"]
        )

        df["closed_at"] = to_utc(
            df["closed_at"]
        )

        df["days_to_close"] = (
            (
                df["closed_at"]
                - df["created_at"]
            )
            .dt
            .total_seconds()
            / 86400
        )

    return df
