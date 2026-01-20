import json
import urllib.request
import urllib.error
import sys
import time

API_URL = "http://localhost:8050/api/species"

FAKE_SPECIES = [
    {
        "name": "Juniperus chinensis",
        "care_guide": {
            "light": "Full sun",
            "water": "Moderate, allow soil to dry slightly",
            "temperature": "Hardy, needs winter dormancy"
        }
    },
    {
        "name": "Pinus thunbergii",
        "care_guide": {
            "light": "Full sun",
            "water": "Well-draining soil, reduce water in winter",
            "temperature": "Outdoor, needs cold winter"
        }
    },
    {
        "name": "Acer palmatum",
        "care_guide": {
            "light": "Partial shade, avoid strong afternoon sun",
            "water": "Keep moist, daily in summer",
            "temperature": "Protect from frost and extreme heat"
        }
    },
    {
        "name": "Ficus retusa",
        "care_guide": {
            "light": "Bright indirect light",
            "water": "Consistent moisture, high humidity",
            "temperature": "Tropical, protect from cold (min 15°C)"
        }
    },
    {
        "name": "Ulmus parvifolia",
        "care_guide": {
            "light": "Full sun to partial shade",
            "water": "Keep moist but not waterlogged",
            "temperature": "Can tolerate some frost, semi-evergreen"
        }
    }
]

def create_species(species_data):
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(species_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print(f"✅ Created: {result['name']} (ID: {result['id']})")
                return True
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to create {species_data['name']}: {e.code} - {e.reason}")
        error_body = e.read().decode('utf-8')
        print(f"   Details: {error_body}")
    except urllib.error.URLError as e:
        print(f"❌ Connection failed: {e.reason}")
        print("   Make sure the API is running at http://localhost:8000")
        sys.exit(1)
    return False

def main():
    print(f"🌱 Populating database via API at {API_URL}...")
    
    # Check if API is alive by creating the first one
    success_count = 0
    for species in FAKE_SPECIES:
        if create_species(species):
            success_count += 1
        time.sleep(0.1) # Be nice to the server

    print(f"\n✨ Finished! Added {success_count}/{len(FAKE_SPECIES)} species.")

if __name__ == "__main__":
    main()
