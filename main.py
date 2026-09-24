from config import (
    GITHUB_TOKEN,
    OWNER,
    REPOSITORIES,
)

from github_client import (
    github_get,
)

from collectors.comments import (
    get_issue_comments,
    get_review_comments,
)

from collectors.commits import (
    get_commits,
)

from collectors.issues import (
    get_issues,
)

from collectors.pull_requests import (
    get_pull_requests,
)

from collectors.reviews import (
    get_reviews,
)

from dashboards.organization_dashboard import (
    build_organization_dashboard,
)

from dashboards.repo_dashboard import (
    build_repo_dashboard,
)

from processing.activity import (
    build_activity_dataframe,
)

from processing.aggregate import (
    aggregate_repositories,
)

from processing.contributors import (
    build_contributor_summary,
)

from processing.filters import (
    clear_excluded_secondary_actor,
    filter_actor_dataframe,
)

from utils.files import (
    ensure_output_directories,
    save_organization_csv,
    save_repo_csv,
)


def get_repo_info(
    owner,
    repo,
):
    data = github_get(
        f"/repos/{owner}/{repo}"
    ).json()

    return {
        "name":
            data["name"],

        "full_name":
            data["full_name"],

        "description":
            data.get(
                "description"
            )
            or "",

        "created_at":
            data["created_at"],

        "updated_at":
            data["updated_at"],

        "default_branch":
            data[
                "default_branch"
            ],

        "stars":
            data[
                "stargazers_count"
            ],

        "forks":
            data[
                "forks_count"
            ],

        "watchers":
            data[
                "subscribers_count"
            ],
    }


def process_repository(
    owner,
    repo,
):
    print()
    print(
        f"Analyzing "
        f"{owner}/{repo}"
    )

    print(
        "Fetching repository "
        "information..."
    )

    repo_info = (
        get_repo_info(
            owner,
            repo,
        )
    )


    print(
        "Fetching commits..."
    )

    commits = get_commits(
        owner,
        repo,
    )

    print(
        f"  Found "
        f"{len(commits):,} "
        "commits before filtering"
    )


    print(
        "Fetching pull requests..."
    )

    prs = get_pull_requests(
        owner,
        repo,
    )

    print(
        f"  Found "
        f"{len(prs):,} "
        "pull requests before filtering"
    )


    print(
        "Fetching issues..."
    )

    issues = get_issues(
        owner,
        repo,
    )

    print(
        f"  Found "
        f"{len(issues):,} "
        "issues before filtering"
    )


    print(
        "Fetching conversation "
        "comments..."
    )

    issue_comments = (
        get_issue_comments(
            owner,
            repo,
        )
    )

    print(
        f"  Found "
        f"{len(issue_comments):,} "
        "conversation comments "
        "before filtering"
    )


    print(
        "Fetching review comments..."
    )

    review_comments = (
        get_review_comments(
            owner,
            repo,
        )
    )

    print(
        f"  Found "
        f"{len(review_comments):,} "
        "review comments "
        "before filtering"
    )


    print(
        "Fetching PR reviews..."
    )

    reviews = get_reviews(
        owner,
        repo,
        prs,
    )

    print(
        f"  Found "
        f"{len(reviews):,} "
        "reviews before filtering"
    )


    print(
        "Filtering program managers, "
        "bots, and automated accounts..."
    )


    commits = (
        filter_actor_dataframe(
            commits,
            "author",
            "author_type",
        )
    )


    prs = (
        filter_actor_dataframe(
            prs,
            "author",
            "author_type",
        )
    )


    issues = (
        filter_actor_dataframe(
            issues,
            "author",
            "author_type",
        )
    )


    issue_comments = (
        filter_actor_dataframe(
            issue_comments,
            "author",
            "author_type",
        )
    )


    review_comments = (
        filter_actor_dataframe(
            review_comments,
            "author",
            "author_type",
        )
    )


    reviews = (
        filter_actor_dataframe(
            reviews,
            "author",
            "author_type",
        )
    )


    # Important:
    #
    # If a student creates a PR and a
    # program manager or bot merges it,
    # keep the student's PR.
    #
    # We only remove attribution for
    # the excluded merger.

    prs = (
        clear_excluded_secondary_actor(
            prs,
            "merged_by",
            "merged_by_type",
        )
    )


    activity = (
        build_activity_dataframe(
            commits,
            prs,
            issues,
            issue_comments,
            review_comments,
            reviews,
        )
    )


    contributors = (
        build_contributor_summary(
            commits,
            prs,
            issues,
            issue_comments,
            review_comments,
            reviews,
        )
    )


    data = {
        "repo_info":
            repo_info,

        "commits":
            commits,

        "prs":
            prs,

        "issues":
            issues,

        "issue_comments":
            issue_comments,

        "review_comments":
            review_comments,

        "reviews":
            reviews,

        "activity":
            activity,

        "contributors":
            contributors,
    }


    print(
        "Saving repository CSVs..."
    )


    save_repo_csv(
        commits,
        repo,
        "commits.csv",
    )


    save_repo_csv(
        prs,
        repo,
        "pull_requests.csv",
    )


    save_repo_csv(
        issues,
        repo,
        "issues.csv",
    )


    save_repo_csv(
        issue_comments,
        repo,
        "conversation_comments.csv",
    )


    save_repo_csv(
        review_comments,
        repo,
        "review_comments.csv",
    )


    save_repo_csv(
        reviews,
        repo,
        "reviews.csv",
    )


    save_repo_csv(
        activity,
        repo,
        "activity.csv",
    )


    save_repo_csv(
        contributors,
        repo,
        "contributors.csv",
    )


    print(
        "Building repository dashboard..."
    )


    dashboard = (
        build_repo_dashboard(
            repo_info,
            data,
        )
    )


    print(
        f"  Dashboard: "
        f"{dashboard}"
    )


    return data


def save_organization_data(
    organization,
):
    mapping = {
        "commits":
            "commits.csv",

        "prs":
            "pull_requests.csv",

        "issues":
            "issues.csv",

        "issue_comments":
            "conversation_comments.csv",

        "review_comments":
            "review_comments.csv",

        "reviews":
            "reviews.csv",

        "activity":
            "activity.csv",

        "contributors":
            "contributors.csv",
    }


    for key, filename in (
        mapping.items()
    ):
        save_organization_csv(
            organization[key],
            filename,
        )


def main():
    ensure_output_directories()


    if not GITHUB_TOKEN:

        print(
            "WARNING: GITHUB_TOKEN "
            "is not set. Public API "
            "requests may work, but "
            "the rate limit will be "
            "much lower."
        )


    repositories = {}


    for repo in REPOSITORIES:

        try:

            repositories[
                repo
            ] = (
                process_repository(
                    OWNER,
                    repo,
                )
            )

        except Exception as exc:

            print()

            print(
                f"ERROR processing "
                f"{OWNER}/{repo}: "
                f"{exc}"
            )

            print(
                "Continuing with the "
                "remaining repositories..."
            )


    if not repositories:

        raise RuntimeError(
            "No repositories were "
            "processed successfully."
        )


    print()

    print(
        "Building combined "
        "organization dataset..."
    )


    organization = (
        aggregate_repositories(
            repositories
        )
    )


    print(
        "Saving combined "
        "organization CSVs..."
    )


    save_organization_data(
        organization
    )


    print(
        "Building organization "
        "dashboard..."
    )


    organization_dashboard = (
        build_organization_dashboard(
            repositories,
            organization,
        )
    )


    print()

    print(
        "Finished."
    )


    print(
        "Organization dashboard: "
        f"{organization_dashboard}"
    )


    print(
        "Individual dashboards are "
        "in reports/"
        "<repo>_dashboard.html"
    )


    print()

    print(
        "On macOS, run:"
    )


    print(
        f"open "
        f"{organization_dashboard}"
    )


if __name__ == "__main__":
    main()
