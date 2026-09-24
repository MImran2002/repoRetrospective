from config import (
    EXCLUDED_BOTS,
    EXCLUDED_USERS,
)


def is_excluded_user(
    username,
):
    if (
        not username
        or str(username).strip() == ""
    ):
        return True

    username_lower = (
        str(username)
        .strip()
        .lower()
    )

    excluded_users = {
        user.lower()
        for user in EXCLUDED_USERS
    }

    excluded_bots = {
        user.lower()
        for user in EXCLUDED_BOTS
    }

    return (
        username_lower
        in excluded_users

        or username_lower
        in excluded_bots

        or username_lower.endswith(
            "[bot]"
        )
    )


def filter_actor_dataframe(
    df,
    actor_column="author",
    type_column=None,
):
    if (
        df.empty
        or actor_column
        not in df.columns
    ):
        return df.copy()

    mask = ~(
        df[actor_column]
        .fillna("")
        .apply(is_excluded_user)
    )

    if (
        type_column
        and type_column
        in df.columns
    ):
        mask &= (
            df[type_column]
            .fillna("")
            .str
            .lower()
            .ne("bot")
        )

    return df.loc[
        mask
    ].copy()


def clear_excluded_secondary_actor(
    df,
    actor_column,
    type_column=None,
):
    """
    Keep the underlying record but remove
    attribution to an excluded secondary actor.

    Example:

    A student creates a PR and a program manager
    merges it. The student's PR should stay in
    the dataset, but the manager should not get
    credit for a teammate merge.
    """

    if (
        df.empty
        or actor_column
        not in df.columns
    ):
        return df.copy()

    df = df.copy()

    mask = (
        df[actor_column]
        .fillna("")
        .apply(is_excluded_user)
    )

    if (
        type_column
        and type_column
        in df.columns
    ):
        mask |= (
            df[type_column]
            .fillna("")
            .str
            .lower()
            .eq("bot")
        )

    df.loc[
        mask,
        actor_column,
    ] = None

    if (
        type_column
        and type_column
        in df.columns
    ):
        df.loc[
            mask,
            type_column,
        ] = None

    return df
