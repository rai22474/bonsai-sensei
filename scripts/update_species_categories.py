import json
import urllib.request
import urllib.error
import sys

API_URL = "http://localhost:8050/api/species"

SPECIES_CATEGORIES = {
    # Conifers
    "Juniperus chinensis": "conifer",
    "Juniperus procumbens": "conifer",
    "Juniperus rigida": "conifer",
    "Juniperus sabina": "conifer",
    "Pinus thunbergii": "conifer",
    "Pinus sylvestris": "conifer",
    "Pinus mugo": "conifer",
    "Pinus pentaphylla": "conifer",
    "Cedrus libani": "conifer",
    "Cedrus atlantica": "conifer",
    "Juniperus chinensis Itoigawa": "conifer",
    "Larix decidua": "conifer",
    "Taxus baccata": "conifer",
    "pino negro japonés": "conifer",
    # Deciduous
    "cerezo de santa lucía": "deciduous",
    "olmo común": "deciduous",
    "arce tridente": "deciduous",
    "Ulmus minor": "deciduous",
    "Fagus sylvatica": "deciduous",
    "Carpinus betulus": "deciduous",
    "Quercus robur": "deciduous",
    "Quercus suber": "deciduous",
    "Betula pendula": "deciduous",
    "Ginkgo biloba": "deciduous",
    "Zelkova serrata": "deciduous",
    "Liquidambar styraciflua": "deciduous",
    # Broadleaf evergreen
    "Buxus sempervirens": "broadleaf",
    "Ilex crenata": "broadleaf",
    "Ligustrum japonicum": "broadleaf",
    "olivos": "broadleaf",
    "Cotoneaster horizontalis": "broadleaf",
    "Pyracantha coccinea": "broadleaf",
    # Flowering
    "Prunus serrulata": "flowering",
    "Prunus mahaleb": "flowering",
    "Azalea": "flowering",
    "Rhododendron indicum": "flowering",
    "Wisteria sinensis": "flowering",
    "Wisteria floribunda": "flowering",
    "Bougainvillea glabra": "flowering",
    "Hibiscus rosa-sinensis": "flowering",
    # Fruiting
    "Granado": "fruiting",
    "Malus sylvestris": "fruiting",
    "Pyrus communis": "fruiting",
    "Citrus limon": "fruiting",
    "Citrus reticulata": "fruiting",
    "Ficus carica": "fruiting",
    "Cydonia oblonga": "fruiting",
    # Tropical
    "Ficus retusa": "tropical",
    "Ficus benjamina": "tropical",
    "Ficus microcarpa": "tropical",
    "Schefflera arboricola": "tropical",
    "Portulacaria afra": "tropical",
    "Serissa foetida": "tropical",
    "Carmona retusa": "tropical",
    "Fukien tea": "tropical",
}


def fetch_all_species() -> list[dict]:
    with urllib.request.urlopen(API_URL) as response:
        return json.loads(response.read().decode("utf-8"))


def update_species_category(species_id: int, category: str) -> bool:
    data = json.dumps({"category": category}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}/{species_id}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.status == 200
    except urllib.error.HTTPError as error:
        print(f"  HTTP {error.code}: {error.read().decode('utf-8')}")
        return False


def main():
    print(f"Fetching species from {API_URL}...")
    try:
        all_species = fetch_all_species()
    except urllib.error.URLError as error:
        print(f"Connection failed: {error.reason}")
        sys.exit(1)

    print(f"Found {len(all_species)} species.\n")

    updated = 0
    skipped = []

    for species in all_species:
        species_id = species["id"]
        name = species["name"]
        current_category = species.get("category", "unknown")
        target_category = SPECIES_CATEGORIES.get(name)

        if target_category is None:
            skipped.append(name)
            continue

        if current_category == target_category:
            print(f"  ✓ {name} already '{target_category}'")
            continue

        success = update_species_category(species_id, target_category)
        if success:
            print(f"  ✅ {name} → {target_category}")
            updated += 1
        else:
            print(f"  ❌ Failed to update {name}")

    print(f"\nUpdated {updated} species.")

    if skipped:
        print(f"\nNo category mapping for {len(skipped)} species — left as 'unknown':")
        for name in skipped:
            print(f"  - {name}")
        print("\nAdd them to SPECIES_CATEGORIES in this script to assign a category.")


if __name__ == "__main__":
    main()
