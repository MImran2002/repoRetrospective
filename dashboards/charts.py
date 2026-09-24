import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plotly.subplots import (
    make_subplots,
)


def empty_figure(
    title,
    message="No data available",
):
    fig = go.Figure()

    fig.update_layout(
        title=title,

        annotations=[
            {
                "text": message,
                "showarrow": False,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
            }
        ],
    )

    return fig


def chart_activity_over_time(
    activity_df,
    title="Repository Activity Over Time",
):
    if activity_df.empty:
        return empty_figure(
            title
        )

    monthly = (
        activity_df
        .groupby(
            [
                "month",
                "activity",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
    )

    return px.line(
        monthly,
        x="month",
        y="count",
        color="activity",
        markers=True,
        title=title,

        labels={
            "month": "Month",
            "count":
                "Activity count",
            "activity":
                "Activity",
        },
    )


def chart_commits_by_contributor(
    summary,
    title="Top Contributors by Commits",
):
    if summary.empty:
        return empty_figure(
            title
        )

    top = (
        summary
        .sort_values(
            "commits",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "commits"
        )
    )

    return px.bar(
        top,

        x="commits",
        y="user",

        orientation="h",

        title=title,

        labels={
            "commits":
                "Commits",
            "user":
                "Contributor",
        },
    )


def chart_pr_status(
    prs,
    title="Pull Request Outcomes",
):
    if prs.empty:
        return empty_figure(
            title
        )

    data = pd.DataFrame({
        "status": [
            "Merged",
            "Open",
            "Closed without merge",
        ],

        "count": [
            int(
                prs["merged"]
                .sum()
            ),

            int(
                prs["state"]
                .eq("open")
                .sum()
            ),

            int(
                prs[
                    "closed_without_merge"
                ]
                .sum()
            ),
        ],
    })

    return px.pie(
        data,

        names="status",
        values="count",

        hole=0.45,

        title=title,
    )


def chart_pr_opened_vs_merged(
    prs,
    title="Pull Requests Opened vs Merged",
):
    if prs.empty:
        return empty_figure(
            title
        )

    opened = (
        prs
        .dropna(
            subset=[
                "created_at"
            ]
        )
        .assign(
            month=lambda x:
            x["created_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby(
            "month"
        )
        .size()
        .rename(
            "Opened"
        )
    )

    merged = (
        prs
        .dropna(
            subset=[
                "merged_at"
            ]
        )
        .assign(
            month=lambda x:
            x["merged_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby(
            "month"
        )
        .size()
        .rename(
            "Merged"
        )
    )

    combined = (
        pd.concat(
            [
                opened,
                merged,
            ],
            axis=1,
        )
        .fillna(0)
        .reset_index()
    )

    melted = combined.melt(
        id_vars="month",
        var_name="type",
        value_name="count",
    )

    return px.line(
        melted,

        x="month",
        y="count",
        color="type",

        markers=True,

        title=title,

        labels={
            "month": "Month",
            "count":
                "Pull requests",
            "type": "",
        },
    )


def chart_issues_opened_vs_closed(
    issues,
    title="Issues Opened vs Closed",
):
    if issues.empty:
        return empty_figure(
            title
        )

    opened = (
        issues
        .dropna(
            subset=[
                "created_at"
            ]
        )
        .assign(
            month=lambda x:
            x["created_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby(
            "month"
        )
        .size()
        .rename(
            "Opened"
        )
    )

    closed = (
        issues
        .dropna(
            subset=[
                "closed_at"
            ]
        )
        .assign(
            month=lambda x:
            x["closed_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby(
            "month"
        )
        .size()
        .rename(
            "Closed"
        )
    )

    combined = (
        pd.concat(
            [
                opened,
                closed,
            ],
            axis=1,
        )
        .fillna(0)
        .reset_index()
    )

    melted = combined.melt(
        id_vars="month",
        var_name="type",
        value_name="count",
    )

    return px.line(
        melted,

        x="month",
        y="count",
        color="type",

        markers=True,

        title=title,

        labels={
            "month": "Month",
            "count": "Issues",
            "type": "",
        },
    )


def chart_reviews_by_contributor(
    summary,
    title="Top Contributors by PR Reviews",
):
    if summary.empty:
        return empty_figure(
            title
        )

    top = (
        summary
        .sort_values(
            "reviews",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "reviews"
        )
    )

    return px.bar(
        top,

        x="reviews",
        y="user",

        orientation="h",

        title=title,

        labels={
            "reviews":
                "Reviews",
            "user":
                "Contributor",
        },
    )


def chart_comments_by_contributor(
    summary,
    title="Top Contributors by Comments",
):
    if summary.empty:
        return empty_figure(
            title
        )

    data = summary.copy()

    data["comments"] = (
        data[
            "conversation_comments"
        ]
        + data[
            "review_comments"
        ]
    )

    top = (
        data
        .sort_values(
            "comments",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "comments"
        )
    )

    return px.bar(
        top,

        x="comments",
        y="user",

        orientation="h",

        title=title,

        labels={
            "comments":
                "Comments",
            "user":
                "Contributor",
        },
    )


def chart_teammate_merges(
    summary,
    title="Who Merged Teammates' Pull Requests",
):
    if summary.empty:
        return empty_figure(
            title
        )

    top = (
        summary
        .sort_values(
            "teammate_prs_merged",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "teammate_prs_merged"
        )
    )

    return px.bar(
        top,

        x="teammate_prs_merged",
        y="user",

        orientation="h",

        title=title,

        labels={
            "teammate_prs_merged":
                "Teammate PRs merged",
            "user":
                "Contributor",
        },
    )


def chart_contributor_breakdown(
    summary,
    title="Contributor Activity Breakdown",
):
    if summary.empty:
        return empty_figure(
            title
        )

    top = (
        summary
        .head(12)
        .copy()
    )

    melted = top.melt(
        id_vars="user",

        value_vars=[
            "commits",
            "prs_opened",
            "reviews",
            "conversation_comments",
            "review_comments",
            "issues_opened",
        ],

        var_name="activity",
        value_name="count",
    )

    labels = {
        "commits":
            "Commits",

        "prs_opened":
            "PRs opened",

        "reviews":
            "Reviews",

        "conversation_comments":
            "Conversation comments",

        "review_comments":
            "Review comments",

        "issues_opened":
            "Issues opened",
    }

    melted["activity"] = (
        melted[
            "activity"
        ]
        .map(labels)
    )

    return px.bar(
        melted,

        x="user",
        y="count",
        color="activity",

        title=title,

        labels={
            "user":
                "Contributor",
            "count":
                "Activity count",
            "activity":
                "Activity",
        },
    )


def chart_pr_merge_time(
    prs,
    title="Median Pull Request Merge Time",
):
    if prs.empty:
        return empty_figure(
            title
        )

    merged = (
        prs
        .dropna(
            subset=[
                "merged_at",
                "days_to_merge",
            ]
        )
        .copy()
    )

    if merged.empty:
        return empty_figure(
            title
        )

    merged["month"] = (
        merged["merged_at"]
        .dt
        .strftime("%Y-%m")
    )

    monthly = (
        merged
        .groupby(
            "month"
        )[
            "days_to_merge"
        ]
        .median()
        .reset_index()
    )

    return px.line(
        monthly,

        x="month",
        y="days_to_merge",

        markers=True,

        title=title,

        labels={
            "month":
                "Month",

            "days_to_merge":
                "Median days to merge",
        },
    )


def chart_code_change(
    prs,
    title="Code Change Through Merged Pull Requests",
):
    if prs.empty:
        return empty_figure(
            title
        )

    merged = (
        prs
        .dropna(
            subset=[
                "merged_at"
            ]
        )
        .copy()
    )

    if merged.empty:
        return empty_figure(
            title
        )

    merged["month"] = (
        merged["merged_at"]
        .dt
        .strftime("%Y-%m")
    )

    monthly = (
        merged
        .groupby(
            "month"
        )[
            [
                "additions",
                "deletions",
                "changed_files",
            ]
        ]
        .sum()
        .reset_index()
    )

    fig = make_subplots(
        rows=2,
        cols=1,

        shared_xaxes=True,

        vertical_spacing=0.12,

        subplot_titles=(
            "Additions and Deletions",
            "Changed Files",
        ),
    )

    fig.add_trace(
        go.Bar(
            x=monthly[
                "month"
            ],
            y=monthly[
                "additions"
            ],
            name="Additions",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=monthly[
                "month"
            ],
            y=monthly[
                "deletions"
            ],
            name="Deletions",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=monthly[
                "month"
            ],
            y=monthly[
                "changed_files"
            ],

            mode=(
                "lines+markers"
            ),

            name=(
                "Changed files"
            ),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title=title,
        barmode="group",
        height=650,
    )

    return fig


def chart_activity_heatmap(
    activity_df,
    title="Repository Activity by Day and Hour (UTC)",
):
    if activity_df.empty:
        return empty_figure(
            title
        )

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    heat = (
        activity_df
        .groupby(
            [
                "weekday",
                "hour",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
        .pivot(
            index="weekday",
            columns="hour",
            values="count",
        )
        .reindex(
            weekday_order
        )
        .fillna(0)
    )

    return px.imshow(
        heat,

        aspect="auto",

        title=title,

        labels={
            "x":
                "Hour (UTC)",

            "y":
                "Day",

            "color":
                "Activity count",
        },
    )


def chart_activity_by_repo(
    activity_df,
):
    if (
        activity_df.empty
        or "repo"
        not in activity_df.columns
    ):
        return empty_figure(
            "Activity by Repository"
        )

    data = (
        activity_df
        .groupby(
            "repo"
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            "count"
        )
    )

    return px.bar(
        data,

        x="count",
        y="repo",

        orientation="h",

        title=(
            "Activity by Repository"
        ),

        labels={
            "count":
                "Activity count",

            "repo":
                "Repository",
        },
    )


def chart_repo_activity_over_time(
    activity_df,
):
    if activity_df.empty:
        return empty_figure(
            "Repository Activity Over Time"
        )

    data = (
        activity_df
        .groupby(
            [
                "month",
                "repo",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
    )

    return px.line(
        data,

        x="month",
        y="count",
        color="repo",

        markers=True,

        title=(
            "Repository Activity Over Time"
        ),

        labels={
            "month":
                "Month",

            "count":
                "Activity count",

            "repo":
                "Repository",
        },
    )


def chart_cross_repo_contributors(
    summary,
):
    if (
        summary.empty
        or "repository_count"
        not in summary.columns
    ):
        return empty_figure(
            "Contributors Active Across Repositories"
        )

    top = (
        summary
        .sort_values(
            [
                "repository_count",
                "total_activity",
            ],
            ascending=False,
        )
        .head(20)
        .sort_values(
            "repository_count"
        )
    )

    return px.bar(
        top,

        x="repository_count",
        y="user",

        orientation="h",

        hover_data=[
            "repositories",
            "total_activity",
        ],

        title=(
            "Contributors Active Across Repositories"
        ),

        labels={
            "repository_count":
                "Repositories",

            "user":
                "Contributor",
        },
    )


def chart_prs_by_repo(
    prs,
):
    if prs.empty:
        return empty_figure(
            "Pull Requests by Repository"
        )

    opened = (
        prs
        .groupby(
            "repo"
        )
        .size()
        .rename(
            "Opened"
        )
    )

    merged = (
        prs.loc[
            prs["merged"]
        ]
        .groupby(
            "repo"
        )
        .size()
        .rename(
            "Merged"
        )
    )

    data = (
        pd.concat(
            [
                opened,
                merged,
            ],
            axis=1,
        )
        .fillna(0)
        .reset_index()
    )

    melted = data.melt(
        id_vars="repo",
        var_name="type",
        value_name="count",
    )

    return px.bar(
        melted,

        x="repo",
        y="count",
        color="type",

        barmode="group",

        title=(
            "Pull Requests by Repository"
        ),

        labels={
            "repo":
                "Repository",

            "count":
                "Pull requests",

            "type":
                "",
        },
    )
