import pandas as pd

from utils.dates import to_utc


def build_activity_dataframe(
    commits,
    prs,
    issues,
    issue_comments,
    review_comments,
    reviews,
):
    rows = []

    def add(
        date,
        user,
        activity,
        repo,
    ):
        rows.append({
            "repo": repo,
            "date": date,
            "user": user,
            "activity": activity,
        })

    for _, row in commits.iterrows():
        add(
            row.get("date"),
            row.get("author"),
            "Commit",
            row.get("repo"),
        )

    for _, row in prs.iterrows():

        add(
            row.get("created_at"),
            row.get("author"),
            "PR opened",
            row.get("repo"),
        )

        if (
            pd.notna(
                row.get("merged_at")
            )
            and row.get("merged_by")
        ):
            add(
                row.get("merged_at"),
                row.get("merged_by"),
                "PR merged",
                row.get("repo"),
            )

    for _, row in issues.iterrows():

        add(
            row.get("created_at"),
            row.get("author"),
            "Issue opened",
            row.get("repo"),
        )

    for _, row in issue_comments.iterrows():

        add(
            row.get("created_at"),
            row.get("author"),
            "Conversation comment",
            row.get("repo"),
        )

    for _, row in review_comments.iterrows():

        add(
            row.get("created_at"),
            row.get("author"),
            "Review comment",
            row.get("repo"),
        )

    for _, row in reviews.iterrows():

        add(
            row.get("submitted_at"),
            row.get("author"),
            "PR review",
            row.get("repo"),
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["date"] = to_utc(
        df["date"]
    )

    df = df.dropna(
        subset=["date"]
    )

    df["month"] = (
        df["date"]
        .dt
        .strftime("%Y-%m")
    )

    df["weekday"] = (
        df["date"]
        .dt
        .day_name()
    )

    df["hour"] = (
        df["date"]
        .dt
        .hour
    )

    return df
