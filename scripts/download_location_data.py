import httpx
import json
import os


def download_location_data():
    base_url = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json"

    data_dir = "seeders/data/location"
    os.makedirs(data_dir, exist_ok=True)

    files = {
        "countries.json": f"{base_url}/countries.json",
        "states.json": f"{base_url}/states.json",
        "cities.json": f"{base_url}/cities.json",
    }

    for filename, url in files.items():
        print(f"Downloading {filename}...")
        try:
            response = httpx.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()

            filepath = os.path.join(data_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"{filename} downloaded ({len(data)} records)")

        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return False

    print("\nAll location data downloaded successfully!")
    print(f"Files saved in: {data_dir}/")
    return True


if __name__ == "__main__":
    download_location_data()
