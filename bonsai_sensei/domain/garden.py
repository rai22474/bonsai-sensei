from typing import List, Dict

# Mock database of user's bonsai collection
_USER_COLLECTION = [
    {"species": "Granado Nejikan (Punica granatum)"},
    {"species": "Azalea (Rhododendron indicum)"},
    {"species": "Olmo Minor (Ulmus minor)"},
    {"species": "Olmo Nire (Zelkova serrata nire)"},
    {"species": "Membrillo japonés (Chaenomeles Chojubai)"},
    {"species": "Pino Negro (Pinus thunbergii)"},
    {"species": "Pino Silvestre (Pinus sylvestris)"},
    {"species": "Pino Blanco (Pinus parviflora)"},
    {"species": "Arce Buergeriano (Acer buergerianum)"},
    {"species": "Arce Yamamomiji (Acer palmatum)"},
    {"species": "Arce Gimnala (Acer tataricum subsp. ginnala)"},
    {"species": "Olivo (Olea europaea)"},
    {"species": "Enebro Chino (Juniperus chinensis 'Itoigawa')"},
    {"species": "Sonare (Juniperus Procumbens Nana)"}
]

def get_all_bonsais() -> List[Dict]:
    """Retrieves all bonsais from the user's collection."""
    return _USER_COLLECTION

def get_all_species() -> List[str]:
    """Retrieves list of unique species from the user's collection."""
    return sorted(list(set(b['species'] for b in _USER_COLLECTION)))
