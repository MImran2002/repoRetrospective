import os
import time
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv
from plotly.subplots import make_subplots


# ============================================================
# Configuration
# ============================================================

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

OWNER = "BCStudentSoftwareDevTeam"
REPO = "celts"

BASE_URL = "https://api.github.com"

DATA_DIR = "data"
REPORTS_DIR = "reports"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ============================================================
# Helpers
# ============================================================

def ensure_output_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def github_get(endpoint, params=None, max_retries=5):
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,

                # 10 sec to connect, 180 sec to receive response
                timeout=(10, 180),
            )

            # GitHub rate limit
            if response.status_code == 403:
                remaining = response.headers.get(
                    "X-RateLimit-Remaining"
                )

                reset = response.headers.get(
                    "X-RateLimit-Reset"
                )

                if remaining == "0" and reset:
                    wait_seconds = max(
                        int(reset) - int(time.time()) + 2,
                        2,
                    )

                    print(
                        f"Rate limit reached. "
                        f"Waiting {wait_seconds} seconds..."
                    )

                    time.sleep(wait_seconds)
                    continue

            response.raise_for_status()

            return response

        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
        ) as error:

            if attempt == max_retries:
                print(
                    f"\nRequest failed after "
                    f"{max_retries} attempts:"
                )

                print(url)
                raise

            wait_seconds = attempt * 5

            print(
                f"\nGitHub request timed out."
                f" Retry {attempt}/{max_retries}"
                f" in {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)


def get_paginated(endpoint, params=None):
    """
    Fetch all pages for a list endpoint.
    """
    params = (params or {}).copy()
    results = []
    page = 1

    while True:
        request_params = params.copy()
        request_params["per_page"] = 100
        request_params["page"] = page

        response = github_get(
            endpoint,
            request_params,
        )

        data = response.json()

        if not data:
            break

        results.extend(data)

        if len(data) < 100:
            break

        page += 1

    return results


def safe_login(user):
    if not user:
        return "Unknown"

    return user.get("login") or "Unknown"


def to_utc(series):
    return pd.to_datetime(
        series,
        utc=True,
        errors="coerce",
    )


def add_month_column(df, date_column, target_column="month"):
    if df.empty or date_column not in df.columns:
        return df

    df = df.copy()

    df[date_column] = to_utc(
        df[date_column]
    )

    df[target_column] = (
        df[date_column]
        .dt
        .strftime("%Y-%m")
    )

    return df


def save_csv(df, filename):
    path = os.path.join(
        DATA_DIR,
        filename,
    )

    df.to_csv(
        path,
        index=False,
    )


# ============================================================
# Repository information
# ============================================================

def get_repo_info():
    repo = github_get(
        f"/repos/{OWNER}/{REPO}"
    ).json()

    return {
        "name": repo["name"],
        "full_name": repo["full_name"],
        "description": repo.get("description") or "",
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "default_branch": repo["default_branch"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "watchers": repo["subscribers_count"],
    }


# ============================================================
# Commits
# ============================================================

def get_commits():
    """
    Fetch commits reachable from the repository's default branch.

    GitHub's commits endpoint uses the default branch when no SHA is supplied.
    """
    commits = get_paginated(
        f"/repos/{OWNER}/{REPO}/commits"
    )

    rows = []

    for commit in commits:
        git_commit = commit.get("commit", {})
        author_data = git_commit.get("author", {})
        committer_data = git_commit.get("committer", {})

        rows.append({
            "sha": commit.get("sha"),
            "author": (
                safe_login(commit.get("author"))
                if commit.get("author")
                else author_data.get("name", "Unknown")
            ),
            "committer": (
                safe_login(commit.get("committer"))
                if commit.get("committer")
                else committer_data.get("name", "Unknown")
            ),
            "date": author_data.get("date"),
            "message": git_commit.get("message", ""),
            "html_url": commit.get("html_url"),
        })

    return pd.DataFrame(rows)


# ============================================================
# Pull requests
# ============================================================

def get_pull_requests():
    """
    Fetch all PRs, then fetch each PR's detail record.

    Detail records provide additions, deletions, changed_files,
    commits count, comments count, review comments, and merged_by.
    """
    prs = get_paginated(
        f"/repos/{OWNER}/{REPO}/pulls",
        {
            "state": "all",
            "sort": "created",
            "direction": "asc",
        }
    )

    rows = []

    total = len(prs)

    for index, pr in enumerate(prs, start=1):
        number = pr["number"]

        if index == 1 or index % 25 == 0 or index == total:
            print(
                f"  PR details: {index}/{total}"
            )

        detail = github_get(
            f"/repos/{OWNER}/{REPO}/pulls/{number}"
        ).json()

        rows.append({
            "number": number,
            "title": detail.get("title", ""),
            "author": safe_login(detail.get("user")),
            "state": detail.get("state"),
            "draft": detail.get("draft", False),
            "created_at": detail.get("created_at"),
            "updated_at": detail.get("updated_at"),
            "closed_at": detail.get("closed_at"),
            "merged_at": detail.get("merged_at"),
            "merged": detail.get("merged", False),
            "merged_by": safe_login(detail.get("merged_by"))
                if detail.get("merged_by")
                else None,
            "additions": detail.get("additions", 0),
            "deletions": detail.get("deletions", 0),
            "changed_files": detail.get("changed_files", 0),
            "commits": detail.get("commits", 0),
            "conversation_comments": detail.get("comments", 0),
            "review_comments": detail.get("review_comments", 0),
            "html_url": detail.get("html_url"),
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
                df["merged_at"] -
                df["created_at"]
            )
            .dt
            .total_seconds()
            / 3600
        )

        df["days_to_merge"] = (
            df["hours_to_merge"] / 24
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


# ============================================================
# Issues
# ============================================================

def get_issues():
    """
    GitHub's issues endpoint also returns pull requests,
    so PR records are filtered out.
    """
    raw_issues = get_paginated(
        f"/repos/{OWNER}/{REPO}/issues",
        {
            "state": "all",
            "sort": "created",
            "direction": "asc",
        }
    )

    rows = []

    for issue in raw_issues:
        if "pull_request" in issue:
            continue

        rows.append({
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "author": safe_login(issue.get("user")),
            "state": issue.get("state"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "closed_at": issue.get("closed_at"),
            "comments_count": issue.get("comments", 0),
            "html_url": issue.get("html_url"),
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
                df["closed_at"] -
                df["created_at"]
            )
            .dt
            .total_seconds()
            / 86400
        )

    return df


# ============================================================
# Repository-wide comments
# ============================================================

def get_issue_comments():
    """
    Includes comments on both Issues and Pull Requests because
    GitHub PR conversation comments use the Issues API.
    """
    comments = get_paginated(
        f"/repos/{OWNER}/{REPO}/issues/comments",
        {
            "sort": "created",
            "direction": "asc",
        }
    )

    rows = []

    for comment in comments:
        rows.append({
            "id": comment.get("id"),
            "author": safe_login(comment.get("user")),
            "created_at": comment.get("created_at"),
            "updated_at": comment.get("updated_at"),
            "issue_url": comment.get("issue_url"),
            "html_url": comment.get("html_url"),
        })

    return pd.DataFrame(rows)


def get_review_comments():
    """
    Inline comments left on PR code diffs.
    """
    comments = get_paginated(
        f"/repos/{OWNER}/{REPO}/pulls/comments",
        {
            "sort": "created",
            "direction": "asc",
        }
    )

    rows = []

    for comment in comments:
        rows.append({
            "id": comment.get("id"),
            "author": safe_login(comment.get("user")),
            "created_at": comment.get("created_at"),
            "updated_at": comment.get("updated_at"),
            "pull_request_url": comment.get("pull_request_url"),
            "html_url": comment.get("html_url"),
        })

    return pd.DataFrame(rows)


# ============================================================
# PR reviews
# ============================================================

def get_reviews(prs):
    """
    Fetch formal PR review submissions.

    This requires one paginated request set per pull request.
    """
    rows = []

    if prs.empty:
        return pd.DataFrame(rows)

    total = len(prs)

    for index, number in enumerate(
        prs["number"],
        start=1,
    ):
        if index == 1 or index % 25 == 0 or index == total:
            print(
                f"  PR reviews: {index}/{total}"
            )

        reviews = get_paginated(
            f"/repos/{OWNER}/{REPO}/pulls/{number}/reviews"
        )

        for review in reviews:
            rows.append({
                "id": review.get("id"),
                "pr_number": number,
                "author": safe_login(review.get("user")),
                "state": review.get("state"),
                "submitted_at": review.get("submitted_at"),
                "html_url": review.get("html_url"),
            })

    return pd.DataFrame(rows)


# ============================================================
# Unified activity table
# ============================================================

def build_activity_dataframe(
    commits,
    prs,
    issues,
    issue_comments,
    review_comments,
    reviews,
):
    rows = []

    if not commits.empty:
        for _, row in commits.iterrows():
            rows.append({
                "date": row["date"],
                "user": row["author"],
                "activity": "Commit",
            })

    if not prs.empty:
        for _, row in prs.iterrows():
            rows.append({
                "date": row["created_at"],
                "user": row["author"],
                "activity": "PR opened",
            })

            if pd.notna(row["merged_at"]):
                rows.append({
                    "date": row["merged_at"],
                    "user": (
                        row["merged_by"]
                        or row["author"]
                    ),
                    "activity": "PR merged",
                })

    if not issues.empty:
        for _, row in issues.iterrows():
            rows.append({
                "date": row["created_at"],
                "user": row["author"],
                "activity": "Issue opened",
            })

            if pd.notna(row["closed_at"]):
                rows.append({
                    "date": row["closed_at"],
                    "user": "Unknown",
                    "activity": "Issue closed",
                })

    if not issue_comments.empty:
        for _, row in issue_comments.iterrows():
            rows.append({
                "date": row["created_at"],
                "user": row["author"],
                "activity": "Conversation comment",
            })

    if not review_comments.empty:
        for _, row in review_comments.iterrows():
            rows.append({
                "date": row["created_at"],
                "user": row["author"],
                "activity": "Review comment",
            })

    if not reviews.empty:
        for _, row in reviews.iterrows():
            rows.append({
                "date": row["submitted_at"],
                "user": row["author"],
                "activity": "PR review",
            })

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


# ============================================================
# Contributor summary
# ============================================================

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
        (commits, "author"),
        (prs, "author"),
        (prs, "merged_by"),
        (issues, "author"),
        (issue_comments, "author"),
        (review_comments, "author"),
        (reviews, "author"),
    ]

    for df, column in datasets:
        if not df.empty and column in df.columns:
            users.update(
                df[column]
                .dropna()
                .astype(str)
                .tolist()
            )

    users.discard("Unknown")

    rows = []

    for user in users:
        commits_count = (
            (commits["author"] == user).sum()
            if not commits.empty
            else 0
        )

        prs_opened = (
            (prs["author"] == user).sum()
            if not prs.empty
            else 0
        )

        own_prs_merged = (
            (
                (prs["author"] == user)
                & prs["merged"]
            ).sum()
            if not prs.empty
            else 0
        )

        teammate_merges = (
            (
                (prs["merged_by"] == user)
                & prs["teammate_merge"]
            ).sum()
            if not prs.empty
            else 0
        )

        issues_opened = (
            (issues["author"] == user).sum()
            if not issues.empty
            else 0
        )

        issue_comment_count = (
            (issue_comments["author"] == user).sum()
            if not issue_comments.empty
            else 0
        )

        review_comment_count = (
            (review_comments["author"] == user).sum()
            if not review_comments.empty
            else 0
        )

        reviews_count = (
            (reviews["author"] == user).sum()
            if not reviews.empty
            else 0
        )

        approvals = (
            (
                (reviews["author"] == user)
                & (
                    reviews["state"]
                    .astype(str)
                    .str
                    .upper()
                    == "APPROVED"
                )
            ).sum()
            if not reviews.empty
            else 0
        )

        rows.append({
            "user": user,
            "commits": int(commits_count),
            "prs_opened": int(prs_opened),
            "own_prs_merged": int(own_prs_merged),
            "teammate_prs_merged": int(teammate_merges),
            "issues_opened": int(issues_opened),
            "conversation_comments": int(issue_comment_count),
            "review_comments": int(review_comment_count),
            "reviews": int(reviews_count),
            "approvals": int(approvals),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["total_activity"] = (
            df[
                [
                    "commits",
                    "prs_opened",
                    "teammate_prs_merged",
                    "issues_opened",
                    "conversation_comments",
                    "review_comments",
                    "reviews",
                ]
            ]
            .sum(axis=1)
        )

        df = df.sort_values(
            "total_activity",
            ascending=False,
        )

    return df


# ============================================================
# Chart creation
# ============================================================

def empty_figure(title, message="No data available"):
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


def chart_activity_over_time(activity_df):
    if activity_df.empty:
        return empty_figure(
            "Repository Activity Over Time"
        )

    monthly = (
        activity_df
        .groupby(
            ["month", "activity"]
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
        title="Repository Activity Over Time",
        labels={
            "month": "Month",
            "count": "Activity count",
            "activity": "Activity",
        },
    )


def chart_commits_by_contributor(summary):
    if summary.empty:
        return empty_figure(
            "Commits by Contributor"
        )

    top = (
        summary
        .sort_values(
            "commits",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "commits",
            ascending=True,
        )
    )

    return px.bar(
        top,
        x="commits",
        y="user",
        orientation="h",
        title="Top Contributors by Commits",
        labels={
            "commits": "Commits",
            "user": "Contributor",
        },
    )


def chart_pr_status(prs):
    if prs.empty:
        return empty_figure(
            "Pull Request Outcomes"
        )

    status_counts = pd.DataFrame({
        "status": [
            "Merged",
            "Open",
            "Closed without merge",
        ],
        "count": [
            int(prs["merged"].sum()),
            int(
                (
                    prs["state"] == "open"
                ).sum()
            ),
            int(
                prs[
                    "closed_without_merge"
                ].sum()
            ),
        ],
    })

    return px.pie(
        status_counts,
        names="status",
        values="count",
        hole=0.45,
        title="Pull Request Outcomes",
    )


def chart_pr_opened_vs_merged(prs):
    if prs.empty:
        return empty_figure(
            "PRs Opened vs Merged"
        )

    opened = (
        prs
        .dropna(subset=["created_at"])
        .assign(
            month=lambda x:
            x["created_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby("month")
        .size()
        .rename("Opened")
    )

    merged = (
        prs
        .dropna(subset=["merged_at"])
        .assign(
            month=lambda x:
            x["merged_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby("month")
        .size()
        .rename("Merged")
    )

    combined = (
        pd.concat(
            [opened, merged],
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
        title="Pull Requests Opened vs Merged",
        labels={
            "month": "Month",
            "count": "Pull requests",
            "type": "",
        },
    )


def chart_issues_opened_vs_closed(issues):
    if issues.empty:
        return empty_figure(
            "Issues Opened vs Closed"
        )

    opened = (
        issues
        .dropna(subset=["created_at"])
        .assign(
            month=lambda x:
            x["created_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby("month")
        .size()
        .rename("Opened")
    )

    closed = (
        issues
        .dropna(subset=["closed_at"])
        .assign(
            month=lambda x:
            x["closed_at"]
            .dt
            .strftime("%Y-%m")
        )
        .groupby("month")
        .size()
        .rename("Closed")
    )

    combined = (
        pd.concat(
            [opened, closed],
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
        title="Issues Opened vs Closed",
        labels={
            "month": "Month",
            "count": "Issues",
            "type": "",
        },
    )


def chart_reviews_by_contributor(summary):
    if summary.empty:
        return empty_figure(
            "Reviews by Contributor"
        )

    top = (
        summary
        .sort_values(
            "reviews",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "reviews",
            ascending=True,
        )
    )

    return px.bar(
        top,
        x="reviews",
        y="user",
        orientation="h",
        title="Top Contributors by PR Reviews",
        labels={
            "reviews": "Reviews",
            "user": "Contributor",
        },
    )


def chart_comments_by_contributor(summary):
    if summary.empty:
        return empty_figure(
            "Comments by Contributor"
        )

    data = summary.copy()

    data["comments"] = (
        data["conversation_comments"]
        + data["review_comments"]
    )

    top = (
        data
        .sort_values(
            "comments",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "comments",
            ascending=True,
        )
    )

    return px.bar(
        top,
        x="comments",
        y="user",
        orientation="h",
        title="Top Contributors by Comments",
        labels={
            "comments": "Comments",
            "user": "Contributor",
        },
    )


def chart_teammate_merges(summary):
    if summary.empty:
        return empty_figure(
            "Teammate PR Merges"
        )

    top = (
        summary
        .sort_values(
            "teammate_prs_merged",
            ascending=False,
        )
        .head(15)
        .sort_values(
            "teammate_prs_merged",
            ascending=True,
        )
    )

    return px.bar(
        top,
        x="teammate_prs_merged",
        y="user",
        orientation="h",
        title="Who Merged Teammates' Pull Requests",
        labels={
            "teammate_prs_merged": "Teammate PRs merged",
            "user": "Contributor",
        },
    )


def chart_contributor_breakdown(summary):
    if summary.empty:
        return empty_figure(
            "Contributor Activity Breakdown"
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
        "commits": "Commits",
        "prs_opened": "PRs opened",
        "reviews": "Reviews",
        "conversation_comments": "Conversation comments",
        "review_comments": "Review comments",
        "issues_opened": "Issues opened",
    }

    melted["activity"] = (
        melted["activity"]
        .map(labels)
    )

    return px.bar(
        melted,
        x="user",
        y="count",
        color="activity",
        title="Contributor Activity Breakdown",
        labels={
            "user": "Contributor",
            "count": "Activity count",
            "activity": "Activity",
        },
    )


def chart_pr_merge_time(prs):
    if prs.empty:
        return empty_figure(
            "Median PR Merge Time"
        )

    merged = prs.dropna(
        subset=[
            "merged_at",
            "days_to_merge",
        ]
    ).copy()

    if merged.empty:
        return empty_figure(
            "Median PR Merge Time"
        )

    merged["month"] = (
        merged["merged_at"]
        .dt
        .strftime("%Y-%m")
    )

    monthly = (
        merged
        .groupby("month")[
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
        title="Median Pull Request Merge Time",
        labels={
            "month": "Month",
            "days_to_merge": "Median days to merge",
        },
    )


def chart_code_change(prs):
    if prs.empty:
        return empty_figure(
            "Code Change Through Merged PRs"
        )

    merged = prs.dropna(
        subset=["merged_at"]
    ).copy()

    if merged.empty:
        return empty_figure(
            "Code Change Through Merged PRs"
        )

    merged["month"] = (
        merged["merged_at"]
        .dt
        .strftime("%Y-%m")
    )

    monthly = (
        merged
        .groupby("month")[
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
            x=monthly["month"],
            y=monthly["additions"],
            name="Additions",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=monthly["month"],
            y=monthly["deletions"],
            name="Deletions",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["changed_files"],
            mode="lines+markers",
            name="Changed files",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="Code Change Through Merged Pull Requests",
        barmode="group",
        height=650,
    )

    return fig


def chart_activity_heatmap(activity_df):
    if activity_df.empty:
        return empty_figure(
            "Activity Heatmap"
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
            ["weekday", "hour"]
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
        title="Repository Activity by Day and Hour (UTC)",
        labels={
            "x": "Hour (UTC)",
            "y": "Day",
            "color": "Activity count",
        },
    )


# ============================================================
# Dashboard HTML
# ============================================================

def figure_html(fig, include_plotlyjs=False):
    return fig.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={
            "responsive": True,
            "displaylogo": False,
        },
    )


def build_dashboard(
    repo_info,
    commits,
    prs,
    issues,
    issue_comments,
    review_comments,
    reviews,
    activity_df,
    contributor_summary,
):
    figures = [
        chart_activity_over_time(
            activity_df
        ),
        chart_contributor_breakdown(
            contributor_summary
        ),
        chart_commits_by_contributor(
            contributor_summary
        ),
        chart_pr_status(
            prs
        ),
        chart_pr_opened_vs_merged(
            prs
        ),
        chart_reviews_by_contributor(
            contributor_summary
        ),
        chart_comments_by_contributor(
            contributor_summary
        ),
        chart_teammate_merges(
            contributor_summary
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
            activity_df
        ),
    ]

    total_comments = (
        len(issue_comments)
        + len(review_comments)
    )

    merged_prs = (
        int(prs["merged"].sum())
        if not prs.empty
        else 0
    )

    contributor_count = (
        len(contributor_summary)
    )

    median_merge_days = (
        prs["days_to_merge"]
        .dropna()
        .median()
        if (
            not prs.empty
            and "days_to_merge"
            in prs.columns
        )
        else float("nan")
    )

    median_merge_text = (
        f"{median_merge_days:.1f} days"
        if pd.notna(median_merge_days)
        else "N/A"
    )

    created = pd.to_datetime(
        repo_info["created_at"],
        utc=True,
    )

    generated = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
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
            f"{contributor_count:,}",
        ),
        (
            "Median PR Merge Time",
            median_merge_text,
        ),
    ]

    kpi_html = "\n".join(
        f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """
        for label, value in kpis
    )

    chart_sections = []

    for index, fig in enumerate(
        figures
    ):
        chart_sections.append(
            f"""
            <section class="chart-card">
                {
                    figure_html(
                        fig,
                        include_plotlyjs=(
                            index == 0
                        ),
                    )
                }
            </section>
            """
        )

    contributor_table = ""

    if not contributor_summary.empty:
        table_df = (
            contributor_summary
            .head(25)
            .copy()
        )

        table_df = table_df.rename(
            columns={
                "user": "Contributor",
                "commits": "Commits",
                "prs_opened": "PRs opened",
                "own_prs_merged": "Own PRs merged",
                "teammate_prs_merged": "Teammate PRs merged",
                "issues_opened": "Issues opened",
                "conversation_comments": "Conversation comments",
                "review_comments": "Review comments",
                "reviews": "Reviews",
                "approvals": "Approvals",
                "total_activity": "Total activity",
            }
        )

        contributor_table = (
            table_df
            .to_html(
                index=False,
                classes="data-table",
                border=0,
            )
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>
        {repo_info["full_name"]} Repository Retrospective
    </title>

    <style>
        :root {{
            --background: #f6f8fa;
            --surface: #ffffff;
            --border: #d0d7de;
            --text: #1f2328;
            --muted: #656d76;
            --accent: #0969da;
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
            background: var(--background);
            color: var(--text);
        }}

        .container {{
            max-width: 1500px;
            margin: 0 auto;
            padding: 32px;
        }}

        header {{
            margin-bottom: 24px;
        }}

        h1 {{
            margin-bottom: 8px;
        }}

        .metadata {{
            color: var(--muted);
            line-height: 1.7;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(180px, 1fr)
                );
            gap: 16px;
            margin: 24px 0;
        }}

        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}

        .kpi-value {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .kpi-label {{
            color: var(--muted);
        }}

        .chart-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(560px, 1fr)
                );
            gap: 18px;
        }}

        .chart-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            min-width: 0;
        }}

        .table-card {{
            margin-top: 18px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
        }}

        .data-table {{
            border-collapse: collapse;
            width: 100%;
        }}

        .data-table th,
        .data-table td {{
            border-bottom: 1px solid var(--border);
            padding: 10px 12px;
            text-align: right;
            white-space: nowrap;
        }}

        .data-table th:first-child,
        .data-table td:first-child {{
            text-align: left;
        }}

        .data-table th {{
            background: #f6f8fa;
        }}

        footer {{
            margin-top: 24px;
            color: var(--muted);
            font-size: 14px;
        }}

        @media (max-width: 700px) {{
            .container {{
                padding: 16px;
            }}

            .chart-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>

<body>
    <main class="container">

        <header>
            <h1>
                {repo_info["full_name"]}
                Repository Retrospective
            </h1>

            <div class="metadata">
                Repository created:
                {created.strftime("%B %d, %Y")}
                <br>

                Default branch:
                <strong>
                    {repo_info["default_branch"]}
                </strong>

                &nbsp;•&nbsp;

                Stars:
                {repo_info["stars"]:,}

                &nbsp;•&nbsp;

                Forks:
                {repo_info["forks"]:,}
            </div>
        </header>

        <section class="kpi-grid">
            {kpi_html}
        </section>

        <section class="chart-grid">
            {''.join(chart_sections)}
        </section>

        <section class="table-card">
            <h2>
                Contributor Breakdown
            </h2>

            <p class="metadata">
                Metrics are shown separately rather than collapsed
                into a single developer score.
            </p>

            {contributor_table}
        </section>

        <footer>
            Generated {generated}.
            Data collected through the GitHub REST API.
        </footer>

    </main>
</body>
</html>
"""

    output_path = os.path.join(
        REPORTS_DIR,
        "dashboard.html",
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(html)

    return output_path


# ============================================================
# Main
# ============================================================

def main():
    ensure_output_directories()

    print(
        f"Analyzing {OWNER}/{REPO}"
    )

    if not TOKEN:
        print(
            "WARNING: GITHUB_TOKEN is not set. "
            "Public API requests will work, but "
            "the rate limit will be much lower."
        )

    print("Fetching repository information...")
    repo_info = get_repo_info()

    print(
        "Repository created:",
        repo_info["created_at"],
    )

    print(
        "Default branch:",
        repo_info["default_branch"],
    )

    print("Fetching commits...")
    commits = get_commits()

    print(
        f"  Found {len(commits):,} commits"
    )

    print("Fetching pull requests...")
    prs = get_pull_requests()

    print(
        f"  Found {len(prs):,} pull requests"
    )

    print("Fetching issues...")
    issues = get_issues()

    print(
        f"  Found {len(issues):,} issues"
    )

    print("Fetching conversation comments...")
    issue_comments = get_issue_comments()

    print(
        f"  Found {len(issue_comments):,} "
        f"conversation comments"
    )

    print("Fetching review comments...")
    review_comments = get_review_comments()

    print(
        f"  Found {len(review_comments):,} "
        f"review comments"
    )

    print("Fetching PR reviews...")
    reviews = get_reviews(prs)

    print(
        f"  Found {len(reviews):,} reviews"
    )

    print("Building activity dataset...")

    activity_df = build_activity_dataframe(
        commits,
        prs,
        issues,
        issue_comments,
        review_comments,
        reviews,
    )

    contributor_summary = (
        build_contributor_summary(
            commits,
            prs,
            issues,
            issue_comments,
            review_comments,
            reviews,
        )
    )

    print("Saving CSV files...")

    save_csv(
        commits,
        "commits.csv",
    )

    save_csv(
        prs,
        "pull_requests.csv",
    )

    save_csv(
        issues,
        "issues.csv",
    )

    save_csv(
        issue_comments,
        "conversation_comments.csv",
    )

    save_csv(
        review_comments,
        "review_comments.csv",
    )

    save_csv(
        reviews,
        "reviews.csv",
    )

    save_csv(
        activity_df,
        "activity.csv",
    )

    save_csv(
        contributor_summary,
        "contributors.csv",
    )

    print("Building dashboard...")

    dashboard_path = build_dashboard(
        repo_info,
        commits,
        prs,
        issues,
        issue_comments,
        review_comments,
        reviews,
        activity_df,
        contributor_summary,
    )

    print()
    print("Finished.")
    print(
        f"Dashboard: {dashboard_path}"
    )
    print()
    print("On macOS, run:")
    print(
        f"open {dashboard_path}"
    )


if __name__ == "__main__":
    main()
