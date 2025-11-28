"""
Admin API Router.
"""
import re
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import (
    Country, Region, Municipality, Flag, User,
    FlagInterest, FlagOwnership, Auction, AuctionStatus
)
from schemas import AdminStatsResponse, MessageResponse
from config import settings

router = APIRouter(tags=["Admin"])


def verify_admin(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key for protected endpoints."""
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin API key"
        )
    return True


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Get overall statistics for the admin panel."""
    total_countries = db.query(func.count(Country.id)).scalar()
    total_regions = db.query(func.count(Region.id)).scalar()
    total_municipalities = db.query(func.count(Municipality.id)).scalar()
    total_flags = db.query(func.count(Flag.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_interests = db.query(func.count(FlagInterest.id)).scalar()
    total_ownerships = db.query(func.count(FlagOwnership.id)).scalar()
    total_auctions = db.query(func.count(Auction.id)).scalar()
    active_auctions = db.query(func.count(Auction.id)).filter(
        Auction.status == AuctionStatus.ACTIVE
    ).scalar()
    completed_pairs = db.query(func.count(Flag.id)).filter(
        Flag.is_pair_complete == True
    ).scalar()

    return AdminStatsResponse(
        total_countries=total_countries or 0,
        total_regions=total_regions or 0,
        total_municipalities=total_municipalities or 0,
        total_flags=total_flags or 0,
        total_users=total_users or 0,
        total_interests=total_interests or 0,
        total_ownerships=total_ownerships or 0,
        total_auctions=total_auctions or 0,
        active_auctions=active_auctions or 0,
        completed_pairs=completed_pairs or 0
    )


@router.post("/seed", response_model=MessageResponse)
def seed_demo_data(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Seed the database with demo data (only if empty)."""
    # Check if data already exists
    existing_countries = db.query(Country).count()
    if existing_countries > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database already has data. Cannot seed."
        )

    # Import seed function
    from seed_data import seed_database
    seed_database(db)

    return MessageResponse(message="Demo data seeded successfully")


@router.post("/reset", response_model=MessageResponse)
def reset_database(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Reset the database (delete all data). USE WITH CAUTION."""
    # Delete in correct order to respect foreign keys
    db.query(FlagInterest).delete()
    db.query(FlagOwnership).delete()
    from models import Bid, UserConnection
    db.query(Bid).delete()
    db.query(Auction).delete()
    db.query(UserConnection).delete()
    db.query(User).delete()
    db.query(Flag).delete()
    db.query(Municipality).delete()
    db.query(Region).delete()
    db.query(Country).delete()
    db.commit()

    return MessageResponse(message="Database reset successfully")


@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.project_name,
        "environment": settings.environment
    }


@router.get("/ipfs-status")
def ipfs_status(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Get IPFS upload status for all flags."""
    total_flags = db.query(func.count(Flag.id)).scalar() or 0
    flags_with_image = db.query(func.count(Flag.id)).filter(
        Flag.image_ipfs_hash.isnot(None)
    ).scalar() or 0
    flags_with_metadata = db.query(func.count(Flag.id)).filter(
        Flag.metadata_ipfs_hash.isnot(None)
    ).scalar() or 0

    return {
        "total_flags": total_flags,
        "flags_with_image_hash": flags_with_image,
        "flags_with_metadata_hash": flags_with_metadata,
        "flags_pending_upload": total_flags - flags_with_image
    }


@router.post("/sync-ipfs-from-pinata", response_model=MessageResponse)
async def sync_ipfs_from_pinata(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    Sync IPFS hashes from Pinata to database flags.
    Matches files by pattern: {COUNTRY_CODE}_{municipality}_{flag_number}.png
    """
    if not settings.pinata_jwt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pinata JWT not configured"
        )

    # Fetch all pinned files from Pinata
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.pinata.cloud/data/pinList",
            params={"status": "pinned", "pageLimit": 1000},
            headers={"Authorization": f"Bearer {settings.pinata_jwt}"},
            timeout=30.0
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch from Pinata: {response.text}"
            )
        pinata_data = response.json()

    # Build mapping of flag_id -> ipfs_hash for images and metadata
    image_map = {}  # {flag_id: ipfs_hash}
    metadata_map = {}  # {flag_id: ipfs_hash}

    for pin in pinata_data.get("rows", []):
        name = pin.get("metadata", {}).get("name", "")
        ipfs_hash = pin.get("ipfs_pin_hash")

        if not name or not ipfs_hash:
            continue

        # Match image files: {COUNTRY_CODE}_{municipality}_{flag_id}.png
        # e.g., ITA_siena_064.png - the number is the flag ID
        match = re.match(r"^[A-Z]{3}_[a-z]+_(\d+)\.png$", name)
        if match:
            flag_id = int(match.group(1))
            image_map[flag_id] = ipfs_hash
            continue

        # Match metadata files: flag_{id}_metadata.json
        match = re.match(r"^flag_(\d+)_metadata\.json$", name)
        if match:
            flag_id = int(match.group(1))
            metadata_map[flag_id] = ipfs_hash

    # Get all flags
    flags = db.query(Flag).all()

    updated_count = 0

    for flag in flags:
        # Find matching image and metadata by flag ID
        image_hash = image_map.get(flag.id)
        metadata_hash = metadata_map.get(flag.id)

        updated = False
        if image_hash and flag.image_ipfs_hash != image_hash:
            flag.image_ipfs_hash = image_hash
            updated = True
        if metadata_hash and flag.metadata_ipfs_hash != metadata_hash:
            flag.metadata_ipfs_hash = metadata_hash
            updated = True

        if updated:
            updated_count += 1

    db.commit()

    return MessageResponse(
        message=f"Synced IPFS hashes. Updated {updated_count} flags. "
                f"Found {len(image_map)} images and {len(metadata_map)} metadata files in Pinata."
    )
