import pandas as pd


def build_contributor_summary(
    commits,
    prs,
    issues,
    issue_comments,
    review_comments,
    reviews,
):
    users = set()

    datasets = [
        (
            commits,
            "author",
        ),
        (
            prs,
            "author",
        ),
        (
            prs,
            "merged_by",
        ),
        (
            issues,
            "author",
        ),
        (
            issue_comments,
            "author",
        ),
        (
            review_comments,
            "author",
        ),
        (
            reviews,
            "author",
        ),
    ]

    for df, column in datasets:

        if (
            not df.empty
            and column
            in df.columns
        ):
            users.update(
                df[column]
                .dropna()
                .astype(str)
                .tolist()
            )

    users.discard(
        "Unknown"
    )

    users.discard(
        ""
    )

    rows = []

    for user in users:

        commits_count = (
            int(
                (
                    commits["author"]
                    == user
                ).sum()
            )
            if not commits.empty
            else 0
        )

        prs_opened = (
            int(
                (
                    prs["author"]
                    == user
                ).sum()
            )
            if not prs.empty
            else 0
        )

        own_prs_merged = (
            int(
                (
                    (
                        prs["author"]
                        == user
                    )
                    & prs["merged"]
                ).sum()
            )
            if not prs.empty
            else 0
        )

        teammate_merges = (
            int(
                (
                    (
                        prs["merged_by"]
                        == user
                    )
                    & prs[
                        "teammate_merge"
                    ]
                ).sum()
            )
            if not prs.empty
            else 0
        )

        issues_opened = (
            int(
                (
                    issues["author"]
                    == user
                ).sum()
            )
            if not issues.empty
            else 0
        )

        issue_comment_count = (
            int(
                (
                    issue_comments[
                        "author"
                    ]
                    == user
                ).sum()
            )
            if not issue_comments.empty
            else 0
        )

        review_comment_count = (
            int(
                (
                    review_comments[
                        "author"
                    ]
                    == user
                ).sum()
            )
            if not review_comments.empty
            else 0
        )

        reviews_count = (
            int(
                (
                    reviews["author"]
                    == user
                ).sum()
            )
            if not reviews.empty
            else 0
        )

        approvals = 0

        if not reviews.empty:
            approvals = int(
                (
                    (
                        reviews["author"]
                        == user
                    )
                    & (
                        reviews["state"]
                        .astype(str)
                        .str
                        .upper()
                        .eq("APPROVED")
                    )
                ).sum()
            )

        repo_set = set()

        for df, column in datasets:

            if (
                not df.empty
                and column
                in df.columns
                and "repo"
                in df.columns
            ):

                repo_set.update(
                    df.loc[
                        df[column] == user,
                        "repo",
                    ]
                    .dropna()
                    .astype(str)
                )

        rows.append({
            "user": user,

            "commits":
                commits_count,

            "prs_opened":
                prs_opened,

            "own_prs_merged":
                own_prs_merged,

            "teammate_prs_merged":
                teammate_merges,

            "issues_opened":
                issues_opened,

            "conversation_comments":
                issue_comment_count,

            "review_comments":
                review_comment_count,

            "reviews":
                reviews_count,

            "approvals":
                approvals,

            "repositories":
                ", ".join(
                    sorted(repo_set)
                ),

            "repository_count":
                len(repo_set),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    metric_columns = [
        "commits",
        "prs_opened",
        "teammate_prs_merged",
        "issues_opened",
        "conversation_comments",
        "review_comments",
        "reviews",
    ]

    df["total_activity"] = (
        df[
            metric_columns
        ]
        .sum(axis=1)
    )

    return (
        df
        .sort_values(
            [
                "total_activity",
                "user",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )
