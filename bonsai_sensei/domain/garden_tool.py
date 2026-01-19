from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.domain import garden

logger = get_logger(__name__)

def get_garden_species() -> str:
    """
    Retrieves the list of unique bonsai species currently in the user's garden.
    Use this to identify which species the user owns to provide specific advice.
    """
    logger.info("Fetching user bonsai garden species")
    try:
        species_list = garden.get_all_species()
        if not species_list:
            return "Your bonsai garden is currently empty."
        
        result = "Species in your Garden:\n" + "\n".join([f"- {s}" for s in species_list])
        logger.info(f"Garden result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error fetching collection: {e}")
        return "Sorry, I couldn't access your bonsai collection at this moment."
