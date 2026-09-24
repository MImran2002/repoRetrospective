import pandas as pd

from github_client import get_paginated


def safe_login(user):
    if not user:
        return "Unknown"

    return user.get("login") or "Unknown"


def get_issue_comments(
    owner,
    repo,
):
    comments = get_paginated(
        f"/repos/{owner}/{repo}/issues/comments",
        {
            "sort": "created",
            "direction": "asc",
        },
    )

    rows = []

    for comment in comments:
        user = comment.get("user") or {}

        rows.append({
            "repo": repo,
            "id": comment.get("id"),
            "author": safe_login(user),
            "author_type": user.get("type"),
            "created_at": comment.get(
                "created_at"
            ),
            "updated_at": comment.get(
                "updated_at"
            ),
            "issue_url": comment.get(
                "issue_url"
            ),
            "html_url": comment.get(
                "html_url"
            ),
        })

    return pd.DataFrame(rows)


def get_review_comments(
    owner,
    repo,
):
    comments = get_paginated(
        f"/repos/{owner}/{repo}/pulls/comments",
        {
            "sort": "created",
            "direction": "asc",
        },
    )

    rows = []

    for comment in comments:
        user = comment.get("user") or {}

        rows.append({
            "repo": repo,
            "id": comment.get("id"),
            "author": safe_login(user),
            "author_type": user.get("type"),
            "created_at": comment.get(
                "created_at"
            ),
            "updated_at": comment.get(
                "updated_at"
            ),
            "pull_request_url": comment.get(
                "pull_request_url"
            ),
            "html_url": comment.get(
                "html_url"
            ),
        })

    return pd.DataFrame(rows)
