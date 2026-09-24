import time

import requests

from config import BASE_URL, HEADERS


def github_get(endpoint, params=None, max_retries=5):
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=(10, 180),
            )

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
        ):
            if attempt == max_retries:
                raise

            wait_seconds = attempt * 5

            print(
                f"GitHub request failed. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)


def get_paginated(endpoint, params=None):
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