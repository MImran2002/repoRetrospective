from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import pandas as pd

from config import REPORTS_DIR

from dashboards.charts import (
    chart_activity_heatmap,
    chart_activity_over_time,
    chart_code_change,
    chart_comments_by_contributor,
    chart_commits_by_contributor,
    chart_contributor_breakdown,
    chart_issues_opened_vs_closed,
    chart_pr_merge_time,
    chart_pr_opened_vs_merged,
    chart_pr_status,
    chart_reviews_by_contributor,
    chart_teammate_merges,
)


def figure_html(
    fig,
    include_plotlyjs=False,
):
    return fig.to_html(
        full_html=False,

        include_plotlyjs=(
            include_plotlyjs
        ),

        config={
            "responsive": True,
            "displaylogo": False,
        },
    )


def _base_html(
    title,
    metadata,
    kpis,
    figures,
    table_html,
    generated,
):
    kpi_html = "\n".join(
        f"""
        <div class="kpi-card">
            <div class="kpi-value">
                {value}
            </div>

            <div class="kpi-label">
                {label}
            </div>
        </div>
        """
        for label, value
        in kpis
    )

    chart_html = "".join(
        f"""
        <section class="chart-card">
            {
                figure_html(
                    fig,
                    include_plotlyjs=(
                        i == 0
                    ),
                )
            }
        </section>
        """
        for i, fig
        in enumerate(figures)
    )

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
    {title}
</title>

<style>

:root {{
    --background: #f6f8fa;
    --surface: #ffffff;
    --border: #d0d7de;
    --text: #1f2328;
    --muted: #656d76;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:
        var(--background);

    color:
        var(--text);
}}

.container {{
    max-width: 1500px;

    margin:
        0 auto;

    padding:
        32px;
}}

.metadata {{
    color:
        var(--muted);

    line-height:
        1.7;
}}

.kpi-grid {{
    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                170px,
                1fr
            )
        );

    gap:
        16px;

    margin:
        24px 0;
}}

.kpi-card,
.chart-card,
.table-card {{
    background:
        var(--surface);

    border:
        1px solid
        var(--border);

    border-radius:
        12px;
}}

.kpi-card {{
    padding:
        20px;
}}

.kpi-value {{
    font-size:
        28px;

    font-weight:
        700;

    margin-bottom:
        6px;
}}

.kpi-label {{
    color:
        var(--muted);
}}

.chart-grid {{
    display:
        grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(
                560px,
                1fr
            )
        );

    gap:
        18px;
}}

.chart-card {{
    padding:
        12px;

    min-width:
        0;
}}

.table-card {{
    margin-top:
        18px;

    padding:
        20px;

    overflow-x:
        auto;
}}

.data-table {{
    border-collapse:
        collapse;

    width:
        100%;
}}

.data-table th,
.data-table td {{
    border-bottom:
        1px solid
        var(--border);

    padding:
        10px 12px;

    text-align:
        right;

    white-space:
        nowrap;
}}

.data-table th:first-child,
.data-table td:first-child {{
    text-align:
        left;
}}

.data-table th {{
    background:
        #f6f8fa;
}}

footer {{
    margin-top:
        24px;

    color:
        var(--muted);

    font-size:
        14px;
}}

@media (
    max-width: 700px
) {{

    .container {{
        padding:
            16px;
    }}

    .chart-grid {{
        grid-template-columns:
            1fr;
    }}
}}

</style>

</head>

<body>

<main class="container">

<header>

<h1>
    {title}
</h1>

<div class="metadata">
    {metadata}
</div>

</header>


<section class="kpi-grid">

{kpi_html}

</section>


<section class="chart-grid">

{chart_html}

</section>


<section class="table-card">

<h2>
    Contributor Breakdown
</h2>

<p class="metadata">
    Program managers and automated/bot accounts
    configured for exclusion are removed before
    these metrics are calculated.
</p>

{table_html}

</section>


<footer>
    Generated {generated}.
    Data collected through the GitHub REST API.
</footer>

</main>

</body>

</html>
"""


def build_repo_dashboard(
    repo_info,
    data,
):
    commits = data[
        "commits"
    ]

    prs = data[
        "prs"
    ]

    issues = data[
        "issues"
    ]

    issue_comments = data[
        "issue_comments"
    ]

    review_comments = data[
        "review_comments"
    ]

    reviews = data[
        "reviews"
    ]

    activity = data[
        "activity"
    ]

    summary = data[
        "contributors"
    ]

    total_comments = (
        len(issue_comments)
        + len(review_comments)
    )

    merged_prs = (
        int(
            prs["merged"]
            .sum()
        )
        if not prs.empty
        else 0
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
            "Contributors",
            f"{len(summary):,}",
        ),

        (
            "Median PR Merge Time",
            median_merge_text,
        ),
    ]

    figures = [
        chart_activity_over_time(
            activity
        ),

        chart_contributor_breakdown(
            summary
        ),

        chart_commits_by_contributor(
            summary
        ),

        chart_pr_status(
            prs
        ),

        chart_pr_opened_vs_merged(
            prs
        ),

        chart_reviews_by_contributor(
            summary
        ),

        chart_comments_by_contributor(
            summary
        ),

        chart_teammate_merges(
            summary
        ),

        chart_issues_opened_vs_closed(
            issues
        ),

        chart_pr_merge_time(
            prs
        ),

        chart_code_change(
            prs
        ),

        chart_activity_heatmap(
            activity
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
            "commits",
            "prs_opened",
            "own_prs_merged",
            "teammate_prs_merged",
            "issues_opened",
            "conversation_comments",
            "review_comments",
            "reviews",
            "approvals",
            "total_activity",
        ]

        table_html = (
            summary[
                columns
            ]
            .head(30)
            .rename(
                columns={
                    "user":
                        "Contributor",

                    "commits":
                        "Commits",

                    "prs_opened":
                        "PRs opened",

                    "own_prs_merged":
                        "Own PRs merged",

                    "teammate_prs_merged":
                        "Teammate PRs merged",

                    "issues_opened":
                        "Issues opened",

                    "conversation_comments":
                        "Conversation comments",

                    "review_comments":
                        "Review comments",

                    "reviews":
                        "Reviews",

                    "approvals":
                        "Approvals",

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

    created = pd.to_datetime(
        repo_info[
            "created_at"
        ],
        utc=True,
    )

    metadata = (
        "Repository created: "
        f"{created.strftime('%B %d, %Y')}"
        "<br>"

        "Default branch: "
        f"<strong>"
        f"{repo_info['default_branch']}"
        f"</strong>"

        " &nbsp;•&nbsp; "

        "Stars: "
        f"{repo_info['stars']:,}"

        " &nbsp;•&nbsp; "

        "Forks: "
        f"{repo_info['forks']:,}"
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
        f"{repo_info['full_name']} "
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
        / (
            f"{repo_info['name']}"
            "_dashboard.html"
        )
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
