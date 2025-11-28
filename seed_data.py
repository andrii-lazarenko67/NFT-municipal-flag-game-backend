"""
Seed database with demo data.

MULTI-NFT FEATURE DOCUMENTATION:
================================
This seed file implements the multi-NFT requirement feature where:
- Most flags require 1 NFT to obtain (standard behavior)
- Premium flags require 3 NFTs to obtain (grouped NFTs)

Design Decision: We use "nfts_required" field to determine how many NFTs
a user must mint/purchase to acquire a flag. This creates a tiered value
system where more prestigious locations (Town Halls = Premium) require
more effort to collect.

Implementation:
- nfts_required=1: User mints/purchases 1 NFT pair to get the flag
- nfts_required=3: User mints/purchases 3 NFT pairs to get the flag

The total cost is calculated as: price * nfts_required
"""
from decimal import Decimal
from sqlalchemy.orm import Session
from models import Country, Region, Municipality, Flag, FlagCategory
from config import settings


def get_nfts_required_for_category(category: FlagCategory) -> int:
    """
    Determine how many NFTs are required based on flag category.

    MULTI-NFT GROUPING LOGIC:
    - PREMIUM flags: Require 3 NFTs (grouped) - most valuable, hardest to obtain
    - PLUS flags: Require 1 NFT - medium value
    - STANDARD flags: Require 1 NFT - basic flags

    This creates a hierarchy where Premium locations like Town Halls
    require more investment to collect.
    """
    if category == FlagCategory.PREMIUM:
        return 3  # Premium flags require 3 NFTs (grouped)
    return 1  # Standard and Plus flags require 1 NFT


# Demo data configuration
# MULTI-NFT FEATURE:
# - Premium (Town Hall) flags require 3 NFTs to obtain (grouped)
# - All other flags require 1 NFT (standard behavior)
DEMO_DATA = {
    "countries": [
        {
            "name": "Spain",
            "code": "ESP",
            "regions": [
                {
                    "name": "Catalonia",
                    "municipalities": [
                        {
                            "name": "Barcelona",
                            "latitude": 41.3851,
                            "longitude": 2.1734,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.STANDARD},
                                {"location_type": "Bakery", "category": FlagCategory.STANDARD},
                                {"location_type": "Church", "category": FlagCategory.PLUS},
                                {"location_type": "Market Square", "category": FlagCategory.STANDARD},
                                {"location_type": "Fountain", "category": FlagCategory.STANDARD},
                                {"location_type": "Bridge", "category": FlagCategory.PLUS},
                                {"location_type": "Park", "category": FlagCategory.STANDARD},
                            ]
                        },
                        {
                            "name": "Girona",
                            "latitude": 41.9794,
                            "longitude": 2.8214,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.STANDARD},
                                {"location_type": "Bakery", "category": FlagCategory.STANDARD},
                                {"location_type": "Church", "category": FlagCategory.PLUS},
                                {"location_type": "Market Square", "category": FlagCategory.STANDARD},
                                {"location_type": "Fountain", "category": FlagCategory.STANDARD},
                                {"location_type": "Bridge", "category": FlagCategory.STANDARD},
                                {"location_type": "Park", "category": FlagCategory.PLUS},
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "name": "France",
            "code": "FRA",
            "regions": [
                {
                    "name": "Provence",
                    "municipalities": [
                        {
                            "name": "Marseille",
                            "latitude": 43.2965,
                            "longitude": 5.3698,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.STANDARD},
                                {"location_type": "Bakery", "category": FlagCategory.PLUS},
                                {"location_type": "Church", "category": FlagCategory.STANDARD},
                                {"location_type": "Market Square", "category": FlagCategory.STANDARD},
                                {"location_type": "Fountain", "category": FlagCategory.PLUS},
                                {"location_type": "Bridge", "category": FlagCategory.STANDARD},
                                {"location_type": "Park", "category": FlagCategory.STANDARD},
                            ]
                        },
                        {
                            "name": "Nice",
                            "latitude": 43.7102,
                            "longitude": 7.2620,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.STANDARD},
                                {"location_type": "Bakery", "category": FlagCategory.STANDARD},
                                {"location_type": "Church", "category": FlagCategory.STANDARD},
                                {"location_type": "Market Square", "category": FlagCategory.PLUS},
                                {"location_type": "Fountain", "category": FlagCategory.STANDARD},
                                {"location_type": "Bridge", "category": FlagCategory.PLUS},
                                {"location_type": "Park", "category": FlagCategory.STANDARD},
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "name": "Germany",
            "code": "DEU",
            "regions": [
                {
                    "name": "Bavaria",
                    "municipalities": [
                        {
                            "name": "Munich",
                            "latitude": 48.1351,
                            "longitude": 11.5820,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.PLUS},
                                {"location_type": "Bakery", "category": FlagCategory.STANDARD},
                                {"location_type": "Church", "category": FlagCategory.STANDARD},
                                {"location_type": "Market Square", "category": FlagCategory.STANDARD},
                                {"location_type": "Fountain", "category": FlagCategory.STANDARD},
                                {"location_type": "Bridge", "category": FlagCategory.STANDARD},
                                {"location_type": "Park", "category": FlagCategory.PLUS},
                            ]
                        },
                        {
                            "name": "Nuremberg",
                            "latitude": 49.4521,
                            "longitude": 11.0767,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.STANDARD},
                                {"location_type": "Bakery", "category": FlagCategory.PLUS},
                                {"location_type": "Church", "category": FlagCategory.STANDARD},
                                {"location_type": "Market Square", "category": FlagCategory.STANDARD},
                                {"location_type": "Fountain", "category": FlagCategory.PLUS},
                                {"location_type": "Bridge", "category": FlagCategory.STANDARD},
                                {"location_type": "Park", "category": FlagCategory.STANDARD},
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "name": "Italy",
            "code": "ITA",
            "regions": [
                {
                    "name": "Tuscany",
                    "municipalities": [
                        {
                            "name": "Florence",
                            "latitude": 43.7696,
                            "longitude": 11.2558,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.STANDARD},
                                {"location_type": "Bakery", "category": FlagCategory.STANDARD},
                                {"location_type": "Church", "category": FlagCategory.PLUS},
                                {"location_type": "Market Square", "category": FlagCategory.PLUS},
                                {"location_type": "Fountain", "category": FlagCategory.STANDARD},
                                {"location_type": "Bridge", "category": FlagCategory.STANDARD},
                                {"location_type": "Park", "category": FlagCategory.STANDARD},
                            ]
                        },
                        {
                            "name": "Siena",
                            "latitude": 43.3188,
                            "longitude": 11.3308,
                            "flags": [
                                {"location_type": "Town Hall", "category": FlagCategory.PREMIUM},
                                {"location_type": "Fire Station", "category": FlagCategory.PLUS},
                                {"location_type": "Bakery", "category": FlagCategory.STANDARD},
                                {"location_type": "Church", "category": FlagCategory.STANDARD},
                                {"location_type": "Market Square", "category": FlagCategory.STANDARD},
                                {"location_type": "Fountain", "category": FlagCategory.STANDARD},
                                {"location_type": "Bridge", "category": FlagCategory.PLUS},
                                {"location_type": "Park", "category": FlagCategory.STANDARD},
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}


def get_price_for_category(category: FlagCategory) -> Decimal:
    """Get price based on category from settings."""
    if category == FlagCategory.STANDARD:
        return Decimal(str(settings.default_standard_price))
    elif category == FlagCategory.PLUS:
        return Decimal(str(settings.default_plus_price))
    elif category == FlagCategory.PREMIUM:
        return Decimal(str(settings.default_premium_price))
    return Decimal(str(settings.default_standard_price))


def seed_database(db: Session):
    """
    Seed the database with demo data.

    MULTI-NFT FEATURE:
    Each flag is assigned an 'nfts_required' value based on its category:
    - Premium flags: 3 NFTs required (grouped NFT acquisition)
    - Plus/Standard flags: 1 NFT required (single NFT acquisition)
    """
    print("🌱 Seeding database with demo data...")
    print("📦 Multi-NFT Feature: Premium flags will require 3 NFTs")

    flag_counter = 0
    premium_count = 0
    standard_count = 0

    for country_data in DEMO_DATA["countries"]:
        # Create country
        country = Country(
            name=country_data["name"],
            code=country_data["code"]
        )
        db.add(country)
        db.flush()  # Get the ID
        print(f"  ✅ Created country: {country.name}")

        for region_data in country_data["regions"]:
            # Create region
            region = Region(
                name=region_data["name"],
                country_id=country.id
            )
            db.add(region)
            db.flush()
            print(f"    ✅ Created region: {region.name}")

            for municipality_data in region_data["municipalities"]:
                # Create municipality
                municipality = Municipality(
                    name=municipality_data["name"],
                    region_id=region.id,
                    latitude=municipality_data["latitude"],
                    longitude=municipality_data["longitude"]
                )
                db.add(municipality)
                db.flush()
                print(f"      ✅ Created municipality: {municipality.name}")

                for i, flag_data in enumerate(municipality_data["flags"]):
                    flag_counter += 1
                    # Create flag with coordinates as name
                    # Add slight offset to coordinates for each flag
                    lat_offset = (i % 4) * 0.001
                    lon_offset = (i // 4) * 0.001
                    flag_lat = municipality_data["latitude"] + lat_offset
                    flag_lon = municipality_data["longitude"] + lon_offset

                    # MULTI-NFT: Determine NFTs required based on category
                    nfts_required = get_nfts_required_for_category(flag_data["category"])

                    if nfts_required > 1:
                        premium_count += 1
                    else:
                        standard_count += 1

                    flag = Flag(
                        municipality_id=municipality.id,
                        name=f"{flag_lat:.6f}, {flag_lon:.6f}",
                        location_type=flag_data["location_type"],
                        category=flag_data["category"],
                        nfts_required=nfts_required,  # MULTI-NFT field
                        price=get_price_for_category(flag_data["category"])
                    )
                    db.add(flag)

                print(f"        ✅ Created 8 flags for {municipality.name}")

    db.commit()
    print(f"\n🎉 Seeding complete!")
    print(f"   📊 Total flags: {flag_counter}")
    print(f"   🔷 Single NFT flags (1 NFT): {standard_count}")
    print(f"   🔶 Grouped NFT flags (3 NFTs): {premium_count}")


def run_seed():
    """Run seed as standalone script."""
    from database import SessionLocal, init_db

    # Initialize database
    init_db()

    # Create session and seed
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Country).count()
        if existing > 0:
            print("⚠️  Database already has data. Skipping seed.")
            return

        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
