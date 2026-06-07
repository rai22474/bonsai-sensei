import re

import aiohttp

from http_client import delete_kb, get_kb, put_kb


def get_wiki_page(path: str) -> dict | None:
    try:
        return get_kb(f"/api/wiki?path={path}")
    except aiohttp.ClientResponseError as error:
        if error.status == 404:
            return None
        raise


def write_wiki_page(path: str, content: str) -> None:
    put_kb("/api/wiki", {"path": path, "content": content})


def delete_wiki_page(path: str) -> None:
    try:
        delete_kb(f"/api/wiki?path={path}")
    except aiohttp.ClientResponseError as error:
        if error.status != 404:
            raise


def delete_bonsai_wiki_pages(bonsai_name: str, user_id: str | None = None) -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    old_paths = [
        f"bonsai/{slug}/index.md",
        f"bonsai/{slug}/fertilization-plan.md",
        f"bonsai/{slug}/phytosanitary-plan.md",
        f"bonsai/{slug}/plans/index.md",
        f"bonsai/{slug}/phytosanitary-plans/index.md",
    ]
    for path in old_paths:
        delete_wiki_page(path)
    if user_id:
        new_paths = [
            f"users/{user_id}/bonsai/{slug}/index.md",
            f"users/{user_id}/bonsai/{slug}/fertilization-plan.md",
            f"users/{user_id}/bonsai/{slug}/phytosanitary-plan.md",
            f"users/{user_id}/bonsai/{slug}/plans/index.md",
            f"users/{user_id}/bonsai/{slug}/phytosanitary-plans/index.md",
            f"users/{user_id}/bonsai/{slug}/design-plans/index.md",
            f"users/{user_id}/bonsai/{slug}/reports/index.md",
        ]
        for path in new_paths:
            delete_wiki_page(path)
