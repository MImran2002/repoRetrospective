import pandas as pd

from github_client import get_paginated


def safe_login(user):
    if not user:
        return "Unknown"

    return user.get("login") or "Unknown"


def get_commits(owner, repo):
    commits = get_paginated(
        f"/repos/{owner}/{repo}/commits"
    )

    rows = []

    for commit in commits:
        git_commit = commit.get("commit", {})

        author_data = git_commit.get(
            "author",
            {},
        )

        committer_data = git_commit.get(
            "committer",
            {},
        )

        github_author = commit.get("author")

        rows.append({
            "repo": repo,
            "sha": commit.get("sha"),

            "author": (
                safe_login(github_author)
                if github_author
                else author_data.get(
                    "name",
                    "Unknown",
                )
            ),

            "author_type": (
                github_author.get("type")
                if github_author
                else None
            ),

            "committer": (
                safe_login(commit.get("committer"))
                if commit.get("committer")
                else committer_data.get(
                    "name",
                    "Unknown",
                )
            ),

            "date": author_data.get("date"),

            "message": git_commit.get(
                "message",
                "",
            ),

            "html_url": commit.get(
                "html_url"
            ),
        })

    return pd.DataFrame(rows)