import aiohttp

from bonsai_sensei.domain.services.garden.bonsai_index_page import build_bonsai_wiki_path


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
    delete_wiki_page(delete_func, build_bonsai_wiki_path(bonsai_name))
