import pandas as pd

from github_client import (
    github_get,
    get_paginated,
)
from utils.dates import to_utc


def safe_login(user):
    if not user:
        return "Unknown"

    return user.get("login") or "Unknown"


def get_pull_requests(
    owner,
    repo,
):
    prs = get_paginated(
        f"/repos/{owner}/{repo}/pulls",
        {
            "state": "all",
            "sort": "created",
            "direction": "asc",
        },
    )

    rows = []

    total = len(prs)

    for index, pr in enumerate(
        prs,
        start=1,
    ):
        number = pr["number"]

        if (
            index == 1
            or index % 25 == 0
            or index == total
        ):
            print(
                f"  PR details: "
                f"{index}/{total}"
            )

        detail = github_get(
            f"/repos/{owner}/{repo}"
            f"/pulls/{number}"
        ).json()

        author = (
            detail.get("user")
            or {}
        )

        merged_by = (
            detail.get("merged_by")
            or {}
        )

        rows.append({
            "repo": repo,
            "number": number,
            "title": detail.get(
                "title",
                "",
            ),
            "author": safe_login(
                author
            ),
            "author_type": author.get(
                "type"
            ),
            "state": detail.get(
                "state"
            ),
            "draft": detail.get(
                "draft",
                False,
            ),
            "created_at": detail.get(
                "created_at"
            ),
            "updated_at": detail.get(
                "updated_at"
            ),
            "closed_at": detail.get(
                "closed_at"
            ),
            "merged_at": detail.get(
                "merged_at"
            ),
            "merged": detail.get(
                "merged",
                False,
            ),
            "merged_by": (
                safe_login(merged_by)
                if merged_by
                else None
            ),
            "merged_by_type": (
                merged_by.get("type")
                if merged_by
                else None
            ),
            "additions": detail.get(
                "additions",
                0,
            ),
            "deletions": detail.get(
                "deletions",
                0,
            ),
            "changed_files": detail.get(
                "changed_files",
                0,
            ),
            "commits": detail.get(
                "commits",
                0,
            ),
            "conversation_comments": (
                detail.get(
                    "comments",
                    0,
                )
            ),
            "review_comments": (
                detail.get(
                    "review_comments",
                    0,
                )
            ),
            "html_url": detail.get(
                "html_url"
            ),
        })

    df = pd.DataFrame(rows)

    if not df.empty:

        df["created_at"] = to_utc(
            df["created_at"]
        )

        df["merged_at"] = to_utc(
            df["merged_at"]
        )

        df["closed_at"] = to_utc(
            df["closed_at"]
        )

        df["hours_to_merge"] = (
            (
                df["merged_at"]
                - df["created_at"]
            )
            .dt
            .total_seconds()
            / 3600
        )

        df["days_to_merge"] = (
            df["hours_to_merge"]
            / 24
        )

        df["closed_without_merge"] = (
            df["closed_at"].notna()
            & df["merged_at"].isna()
        )

        df["teammate_merge"] = (
            df["merged"]
            & df["merged_by"].notna()
            & (
                df["merged_by"]
                != df["author"]
            )
        )

    return df
