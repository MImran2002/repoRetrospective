import os
import requests
import pandas as pd
import plotly.express as px

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

OWNER = "BCStudentSoftwareDevTeam"
REPO = "celts"

BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def github_get(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
    )

    response.raise_for_status()

    return response


def get_paginated(endpoint, params=None):
    if params is None:
        params = {}

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


def get_repo_info():
    response = github_get(
        f"/repos/{OWNER}/{REPO}"
    )

    repo = response.json()

    return {
        "name": repo["name"],
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "open_issues": repo["open_issues_count"],
    }


def get_commits():
    commits = get_paginated(
        f"/repos/{OWNER}/{REPO}/commits"
    )

    rows = []

    for commit in commits:
        github_author = commit.get("author")

        if github_author:
            author = github_author.get("login")
        else:
            author = commit["commit"]["author"]["name"]

        rows.append({
            "sha": commit["sha"],
            "author": author,
            "date": commit["commit"]["author"]["date"],
            "message": commit["commit"]["message"],
        })

    return pd.DataFrame(rows)


def get_pull_requests():
    prs = get_paginated(
        f"/repos/{OWNER}/{REPO}/pulls",
        {
            "state": "all",
        }
    )

    rows = []

    for pr in prs:
        rows.append({
            "number": pr["number"],
            "author": pr["user"]["login"],
            "created_at": pr["created_at"],
            "closed_at": pr["closed_at"],
            "merged_at": pr["merged_at"],
            "state": pr["state"],
        })

    return pd.DataFrame(rows)


def get_issues():
    issues = get_paginated(
        f"/repos/{OWNER}/{REPO}/issues",
        {
            "state": "all",
        }
    )

    rows = []

    for issue in issues:

        # GitHub issues API also returns PRs
        if "pull_request" in issue:
            continue

        rows.append({
            "number": issue["number"],
            "author": issue["user"]["login"],
            "created_at": issue["created_at"],
            "closed_at": issue["closed_at"],
            "state": issue["state"],
            "comments": issue["comments"],
        })

    return pd.DataFrame(rows)


def build_activity_dataframe(
    commits,
    prs,
    issues,
):
    activity = []

    if not commits.empty:
        for _, commit in commits.iterrows():
            activity.append({
                "date": commit["date"],
                "user": commit["author"],
                "activity": "Commit",
            })

    if not prs.empty:
        for _, pr in prs.iterrows():

            activity.append({
                "date": pr["created_at"],
                "user": pr["author"],
                "activity": "Pull Request",
            })

            if pd.notna(pr["merged_at"]):
                activity.append({
                    "date": pr["merged_at"],
                    "user": pr["author"],
                    "activity": "Merged PR",
                })

    if not issues.empty:
        for _, issue in issues.iterrows():

            activity.append({
                "date": issue["created_at"],
                "user": issue["author"],
                "activity": "Issue",
            })

    df = pd.DataFrame(activity)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        utc=True,
    )

    df["month"] = (
        df["date"]
        .dt
        .to_period("M")
        .astype(str)
    )

    return df


def create_activity_chart(activity_df):
    if activity_df.empty:
        print("No activity available for chart.")
        return

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

    fig = px.line(
        monthly,
        x="month",
        y="count",
        color="activity",
        markers=True,
        title="Repository Activity Over Time",
    )

    fig.write_html(
        "reports/activity_over_time.html"
    )


def main():
    print(
        f"Analyzing {OWNER}/{REPO}"
    )

    repo_info = get_repo_info()

    print(
        f"Repository created: "
        f"{repo_info['created_at']}"
    )

    print("Fetching commits...")
    commits = get_commits()

    print("Fetching pull requests...")
    prs = get_pull_requests()

    print("Fetching issues...")
    issues = get_issues()

    commits.to_csv(
        "data/commits.csv",
        index=False,
    )

    prs.to_csv(
        "data/pull_requests.csv",
        index=False,
    )

    issues.to_csv(
        "data/issues.csv",
        index=False,
    )

    activity_df = build_activity_dataframe(
        commits,
        prs,
        issues,
    )

    activity_df.to_csv(
        "data/activity.csv",
        index=False,
    )

    create_activity_chart(
        activity_df
    )

    print()
    print("Finished.")
    print(
        f"Commits: {len(commits)}"
    )
    print(
        f"Pull Requests: {len(prs)}"
    )
    print(
        f"Issues: {len(issues)}"
    )

    print(
        "Open reports/activity_over_time.html"
    )


if __name__ == "__main__":
    main()
