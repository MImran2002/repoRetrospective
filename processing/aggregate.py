import pandas as pd

from processing.activity import (
    build_activity_dataframe,
)
from processing.contributors import (
    build_contributor_summary,
)


DATASET_NAMES = [
    "commits",
    "prs",
    "issues",
    "issue_comments",
    "review_comments",
    "reviews",
]


def combine_dataset(
    repositories,
    dataset_name,
):
    frames = []

    for repo_data in (
        repositories.values()
    ):

        df = repo_data.get(
            dataset_name
        )

        if (
            df is not None
            and not df.empty
        ):
            frames.append(
                df
            )

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )


def aggregate_repositories(
    repositories,
):
    combined = {
        name: combine_dataset(
            repositories,
            name,
        )
        for name
        in DATASET_NAMES
    }

    combined["activity"] = (
        build_activity_dataframe(
            combined["commits"],
            combined["prs"],
            combined["issues"],
            combined[
                "issue_comments"
            ],
            combined[
                "review_comments"
            ],
            combined["reviews"],
        )
    )

    combined["contributors"] = (
        build_contributor_summary(
            combined["commits"],
            combined["prs"],
            combined["issues"],
            combined[
                "issue_comments"
            ],
            combined[
                "review_comments"
            ],
            combined["reviews"],
        )
    )

    return combined
