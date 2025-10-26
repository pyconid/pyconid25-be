import json
import os
from sqlalchemy.orm import Session
from models.Country import Country
from models.State import State
from models.City import City


def initial_country_city_state_seeders(db: Session, is_commit: bool = True):
    data_dir = "seeders/data/location"

    if not os.path.exists(data_dir):
        print(f"\nERROR: Directory '{data_dir}' not found!")
        print("Please run: python cli.py download-location-data\n")
        raise FileNotFoundError(f"Directory {data_dir} not found")

    print("\nLoading countries...")
    with open(f"{data_dir}/countries.json", "r", encoding="utf-8") as f:
        countries_data = json.load(f)

    print("Loading states...")
    with open(f"{data_dir}/states.json", "r", encoding="utf-8") as f:
        states_data = json.load(f)

    print("Loading cities...")
    with open(f"{data_dir}/cities.json", "r", encoding="utf-8") as f:
        cities_data = json.load(f)

    print("\nData Summary:")
    print(f" - Countries: {len(countries_data)}")
    print(f" - States: {len(states_data)}")
    print(f" - Cities: {len(cities_data)}")

    print(f"\nUpserting {len(countries_data)} countries...")
    upserted_countries = 0
    for country_data in countries_data:
        country = Country(
            id=country_data.get("id"),
            name=country_data.get("name"),
            iso3=country_data.get("iso3"),
            iso2=country_data.get("iso2"),
            numeric_code=country_data.get("numeric_code"),
            phone_code=country_data.get("phone_code"),
            capital=country_data.get("capital"),
            currency=country_data.get("currency"),
            currency_name=country_data.get("currency_name"),
            currency_symbol=country_data.get("currency_symbol"),
            tld=country_data.get("tld"),
            native=country_data.get("native"),
            region=country_data.get("region"),
            subregion=country_data.get("subregion"),
            nationality=country_data.get("nationality"),
            timezones=country_data.get("timezones"),
            translations=country_data.get("translations"),
            latitude=country_data.get("latitude"),
            longitude=country_data.get("longitude"),
            emoji=country_data.get("emoji"),
            emojiU=country_data.get("emojiU"),
        )
        db.merge(country)
        upserted_countries += 1

        if upserted_countries % 50 == 0:
            if is_commit:
                db.commit()
            print(f"   Upserted {upserted_countries} countries...")

    if is_commit:
        db.commit()
    print(f"   Total countries upserted: {upserted_countries}")

    print(f"\nUpserting {len(states_data)} states...")
    upserted_states = 0
    for state_data in states_data:
        state = State(
            id=state_data.get("id"),
            name=state_data.get("name"),
            country_id=state_data.get("country_id"),
            country_code=state_data.get("country_code"),
            fips_code=state_data.get("fips_code"),
            iso2=state_data.get("iso2"),
            type=state_data.get("type"),
            latitude=state_data.get("latitude"),
            longitude=state_data.get("longitude"),
        )
        db.merge(state)
        upserted_states += 1

        if upserted_states % 100 == 0:
            if is_commit:
                db.commit()
            print(f"   Upserted {upserted_states} states...")

    if is_commit:
        db.commit()
    print(f"   Total states upserted: {upserted_states}")

    print(f"\nUpserting {len(cities_data)} cities...")
    upserted_cities = 0
    for city_data in cities_data:
        city = City(
            id=city_data.get("id"),
            name=city_data.get("name"),
            state_id=city_data.get("state_id"),
            state_code=city_data.get("state_code"),
            country_id=city_data.get("country_id"),
            country_code=city_data.get("country_code"),
            latitude=city_data.get("latitude"),
            longitude=city_data.get("longitude"),
            wikiDataId=city_data.get("wikiDataId"),
        )
        db.merge(city)
        upserted_cities += 1

        if upserted_cities % 500 == 0:
            if is_commit:
                db.commit()
            print(f"   Upserted {upserted_cities} cities...")

    if is_commit:
        db.commit()
    print(f"   Total cities upserted: {upserted_cities}")

    print("\nSummary:")
    print(f"  Countries: {upserted_countries}")
    print(f"  States: {upserted_states}")
    print(f"  Cities: {upserted_cities}")
    print()

    return {
        "countries": upserted_countries,
        "states": upserted_states,
        "cities": upserted_cities,
    }


def clear_data_location(db: Session, is_commit: bool = True):
    print("Deleting cities...")
    db.query(City).delete()

    print("Deleting states...")
    db.query(State).delete()

    print("Deleting countries...")
    db.query(Country).delete()

    if is_commit:
        db.commit()

    print("All location data cleared!")
