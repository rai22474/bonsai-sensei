import re


def build_bonsai_wiki_path(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"bonsai/{slug}/index.md"


def build_bonsai_index_page(name: str, species_name: str, species_wiki_path: str | None) -> str:
    if species_wiki_path:
        species_line = f"[[{species_wiki_path}|{species_name}]]"
    else:
        species_line = species_name

    return f"""# {name}

**Especie:** {species_line}

## Páginas relacionadas
"""
