import os

from dotenv import load_dotenv


load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

OWNER = "BCStudentSoftwareDevTeam"

REPOSITORIES = [
    "bcsr",
    "celts",
    "lsf",
    "urcpp",
    "cas",
]

BASE_URL = "https://api.github.com"

DATA_DIR = "data"
REPORTS_DIR = "reports"


# Humans whose activity should not be included in
# student-programmer contribution analytics.
EXCLUDED_USERS = {
    # Example:
    # "program-manager-github-username",
    "BrianRamsay",
    "sheggen"
}


# Accounts that should always be excluded.
EXCLUDED_BOTS = {
    "github-actions[bot]",
    "dependabot[bot]",
    "dependabot-preview[bot]",
    "renovate[bot]",
    "copilot-pull-request-reviewer[bot]",
}


HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"