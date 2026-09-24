from pathlib import Path

from config import DATA_DIR, REPORTS_DIR


def ensure_output_directories():
    Path(DATA_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(REPORTS_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )


def save_repo_csv(
    df,
    repo,
    filename,
):
    directory = Path(DATA_DIR) / repo

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = directory / filename

    df.to_csv(
        path,
        index=False,
    )

    return path


def save_organization_csv(
    df,
    filename,
):
    return save_repo_csv(
        df,
        "organization",
        filename,
    )
