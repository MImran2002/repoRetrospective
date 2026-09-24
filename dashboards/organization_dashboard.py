from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pandas as pd

from config import (
    OWNER,
    REPORTS_DIR,
)

from dashboards.charts import (
    chart_activity_by_repo,
    chart_activity_heatmap,
    chart_activity_over_time,
    chart_comments_by_contributor,
    chart_commits_by_contributor,
    chart_cross_repo_contributors,
    chart_pr_merge_time,
    chart_prs_by_repo,
    chart_repo_activity_over_time,
    chart_reviews_by_contributor,
)

from dashboards.repo_dashboard import (
    _base_html,
)


def build_organization_dashboard(
    repositories,
    organization,
):
    commits = organization[
        "commits"
    ]

    prs = organization[
        "prs"
    ]

    issues = organization[
        "issues"
    ]

    issue_comments = organization[
        "issue_comments"
    ]

    review_comments = organization[
        "review_comments"
    ]

    reviews = organization[
        "reviews"
    ]

    activity = organization[
        "activity"
    ]

    summary = organization[
        "contributors"
    ]

    merged_prs = (
        int(
            prs["merged"]
            .sum()
        )

        if not prs.empty

        else 0
    )

    total_comments = (
        len(issue_comments)
        + len(review_comments)
    )

    median_merge_days = (
        prs[
            "days_to_merge"
        ]
        .dropna()
        .median()

        if not prs.empty

        else float(
            "nan"
        )
    )

    median_merge_text = (
        f"{median_merge_days:.1f} days"

        if pd.notna(
            median_merge_days
        )

        else "N/A"
    )

    kpis = [
        (
            "Repositories",
            f"{len(repositories):,}",
        ),

        (
            "Commits",
            f"{len(commits):,}",
        ),

        (
            "Pull Requests",
            f"{len(prs):,}",
        ),

        (
            "Merged PRs",
            f"{merged_prs:,}",
        ),

        (
            "Issues",
            f"{len(issues):,}",
        ),

        (
            "Comments",
            f"{total_comments:,}",
        ),

        (
            "Reviews",
            f"{len(reviews):,}",
        ),

        (
            "Unique Contributors",
            f"{len(summary):,}",
        ),

        (
            "Median PR Merge Time",
            median_merge_text,
        ),
    ]

    figures = [
        chart_repo_activity_over_time(
            activity
        ),

        chart_activity_by_repo(
            activity
        ),

        chart_prs_by_repo(
            prs
        ),

        chart_activity_over_time(
            activity,
            (
                "All SSDT Activity "
                "by Type Over Time"
            ),
        ),

        chart_cross_repo_contributors(
            summary
        ),

        chart_commits_by_contributor(
            summary,
            (
                "Top Contributors by "
                "Commits Across All "
                "Repositories"
            ),
        ),

        chart_reviews_by_contributor(
            summary,
            (
                "Top Reviewers Across "
                "All Repositories"
            ),
        ),

        chart_comments_by_contributor(
            summary,
            (
                "Top Commenters Across "
                "All Repositories"
            ),
        ),

        chart_pr_merge_time(
            prs,
            (
                "Organization-wide "
                "Median PR Merge Time"
            ),
        ),

        chart_activity_heatmap(
            activity,
            (
                "All SSDT Activity by "
                "Day and Hour (UTC)"
            ),
        ),
    ]

    table_html = (
        "<p>"
        "No contributor data available."
        "</p>"
    )

    if not summary.empty:

        columns = [
            "user",
            "repository_count",
            "repositories",
            "commits",
            "prs_opened",
            "issues_opened",
            "conversation_comments",
            "review_comments",
            "reviews",
            "teammate_prs_merged",
            "total_activity",
        ]

        table_html = (
            summary[
                columns
            ]
            .head(50)
            .rename(
                columns={
                    "user":
                        "Contributor",

                    "repository_count":
                        "Repo count",

                    "repositories":
                        "Repositories",

                    "commits":
                        "Commits",

                    "prs_opened":
                        "PRs opened",

                    "issues_opened":
                        "Issues opened",

                    "conversation_comments":
                        "Conversation comments",

                    "review_comments":
                        "Review comments",

                    "reviews":
                        "Reviews",

                    "teammate_prs_merged":
                        "Teammate PRs merged",

                    "total_activity":
                        "Total activity",
                }
            )
            .to_html(
                index=False,
                classes=(
                    "data-table"
                ),
                border=0,
            )
        )

    metadata = (
        "Combined analytics for "
        f"<strong>{OWNER}</strong>: "

        + ", ".join(
            sorted(
                repositories.keys()
            )
        )

        + "."

        "<br>"

        "Metrics are calculated from "
        "the combined filtered raw "
        "datasets, not by adding "
        "repository-level medians or "
        "contributor counts."
    )

    generated = (
        datetime
        .now(
            timezone.utc
        )
        .strftime(
            "%Y-%m-%d "
            "%H:%M UTC"
        )
    )

    title = (
        f"{OWNER} Organization "
        "Repository Retrospective"
    )

    html = _base_html(
        title,
        metadata,
        kpis,
        figures,
        table_html,
        generated,
    )

    output_path = (
        Path(
            REPORTS_DIR
        )
        / "organization_dashboard.html"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        html,
        encoding="utf-8",
    )

    return str(
        output_path
    )
