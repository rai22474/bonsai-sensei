import re


def build_bonsai_wiki_path(name: str, user_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"users/{user_id}/bonsai/{slug}/index.md"


def build_bonsai_index_page(name: str, species_name: str, species_wiki_path: str | None, user_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    species_line = f"[[{species_wiki_path}|{species_name}]]" if species_wiki_path else species_name

    return f"""# {name}

**Especie:** {species_line}

## Páginas relacionadas

- [[users/{user_id}/bonsai/{slug}/plans/index.md|Planes de fertilización]]
- [[users/{user_id}/bonsai/{slug}/reports/index.md|Informes y análisis]]
"""
