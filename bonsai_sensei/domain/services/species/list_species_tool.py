from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.domain import garden

logger = get_logger(__name__)


def _fetch_species_list(get_all_species_func):
    logger.info("Fetching user bonsai garden species")
    try:
        species_list = get_all_species_func()
        logger.info("Garden result count: %s", len(species_list))
        return species_list
    except Exception as e:
        logger.error(f"Error fetching collection: {e}")
        return []


def _format_species_list(species_list) -> str:
    if not species_list:
        return "No hay especies registradas."
    
    formatted = [
        f"- {item['common_name']} ({item['scientific_name']})"
        for item in species_list
    ]
    
    return "Especies registradas:\n" + "\n".join(formatted)


def create_list_bonsai_species_tool(get_all_species_func):
    def list_bonsai_species() -> str:
        """List bonsai species with common and scientific names in a readable format."""
        species_list = _fetch_species_list(get_all_species_func)
        return _format_species_list(species_list)

    return list_bonsai_species
