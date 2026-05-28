import re

import aiohttp


def get_wiki_page(get_func, path: str) -> dict | None:
    try:
        return get_func(f"/api/wiki?path={path}")
    except aiohttp.ClientResponseError as error:
        if error.status == 404:
            return None
        raise


def delete_wiki_page(delete_func, path: str) -> None:
    try:
        delete_func(f"/api/wiki?path={path}")
    except aiohttp.ClientResponseError as error:
        if error.status != 404:
            raise


def delete_bonsai_wiki_pages(delete_func, bonsai_name: str) -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    for path in [
        f"bonsai/{slug}/index.md",
        f"bonsai/{slug}/fertilization-plan.md",
        f"bonsai/{slug}/phytosanitary-plan.md",
        f"bonsai/{slug}/plans/index.md",
        f"bonsai/{slug}/phytosanitary-plans/index.md",
    ]:
        delete_wiki_page(delete_func, path)
