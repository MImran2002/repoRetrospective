import pandas as pd

from github_client import get_paginated


def safe_login(user):
    if not user:
        return "Unknown"

    return user.get("login") or "Unknown"


def get_reviews(
    owner,
    repo,
    prs,
):
    rows = []

    if prs.empty:
        return pd.DataFrame(rows)

    total = len(prs)

    for index, number in enumerate(
        prs["number"],
        start=1,
    ):

        if (
            index == 1
            or index % 25 == 0
            or index == total
        ):
            print(
                f"  PR reviews: "
                f"{index}/{total}"
            )

        reviews = get_paginated(
            f"/repos/{owner}/{repo}"
            f"/pulls/{number}/reviews"
        )

        for review in reviews:
            user = (
                review.get("user")
                or {}
            )

            rows.append({
                "repo": repo,
                "id": review.get("id"),
                "pr_number": number,
                "author": safe_login(user),
                "author_type": user.get(
                    "type"
                ),
                "state": review.get(
                    "state"
                ),
                "submitted_at": review.get(
                    "submitted_at"
                ),
                "html_url": review.get(
                    "html_url"
                ),
            })

    return pd.DataFrame(rows)
