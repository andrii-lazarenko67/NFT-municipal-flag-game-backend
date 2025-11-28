"""
Regions API Router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from database import get_db
from models import Region, Country
from schemas import (
    RegionCreate, RegionUpdate, RegionResponse,
    RegionDetailResponse, CountryResponse, MessageResponse
)
from config import settings

router = APIRouter(tags=["Regions"])


def verify_admin(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key for protected endpoints."""
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin API key"
        )
    return True


@router.get("", response_model=List[RegionResponse])
def get_regions(
    country_id: Optional[int] = None,
    visible_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all regions, optionally filtered by country."""
    query = db.query(Region)

    if country_id:
        query = query.filter(Region.country_id == country_id)
    if visible_only:
        query = query.filter(Region.is_visible == True)

    regions = query.order_by(Region.name).all()

    result = []
    for region in regions:
        result.append(RegionResponse(
            id=region.id,
            name=region.name,
            country_id=region.country_id,
            is_visible=region.is_visible,
            created_at=region.created_at,
            municipality_count=len([m for m in region.municipalities if m.is_visible or not visible_only])
        ))

    return result


@router.get("/{region_id}", response_model=RegionDetailResponse)
def get_region(
    region_id: int,
    db: Session = Depends(get_db)
):
    """Get a single region with its municipalities."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with id {region_id} not found"
        )

    # Build country response
    country_data = CountryResponse(
        id=region.country.id,
        name=region.country.name,
        code=region.country.code,
        is_visible=region.country.is_visible,
        created_at=region.country.created_at,
        region_count=len(region.country.regions)
    )

    # Build municipalities list
    municipalities_data = []
    for municipality in region.municipalities:
        if municipality.is_visible:
            municipalities_data.append({
                "id": municipality.id,
                "name": municipality.name,
                "region_id": municipality.region_id,
                "latitude": municipality.latitude,
                "longitude": municipality.longitude,
                "coordinates": municipality.coordinates,
                "is_visible": municipality.is_visible,
                "created_at": municipality.created_at,
                "flag_count": len([f for f in municipality.flags])
            })

    return RegionDetailResponse(
        id=region.id,
        name=region.name,
        country_id=region.country_id,
        is_visible=region.is_visible,
        created_at=region.created_at,
        municipality_count=len(municipalities_data),
        country=country_data,
        municipalities=municipalities_data
    )


@router.post("", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
def create_region(
    region: RegionCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Create a new region (admin only)."""
    # Verify country exists
    country = db.query(Country).filter(Country.id == region.country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with id {region.country_id} not found"
        )

    db_region = Region(
        name=region.name,
        country_id=region.country_id,
        is_visible=region.is_visible
    )
    db.add(db_region)
    db.commit()
    db.refresh(db_region)

    return RegionResponse(
        id=db_region.id,
        name=db_region.name,
        country_id=db_region.country_id,
        is_visible=db_region.is_visible,
        created_at=db_region.created_at,
        municipality_count=0
    )


@router.put("/{region_id}", response_model=RegionResponse)
def update_region(
    region_id: int,
    region: RegionUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Update a region (admin only)."""
    db_region = db.query(Region).filter(Region.id == region_id).first()
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with id {region_id} not found"
        )

    if region.name is not None:
        db_region.name = region.name
    if region.country_id is not None:
        # Verify new country exists
        country = db.query(Country).filter(Country.id == region.country_id).first()
        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Country with id {region.country_id} not found"
            )
        db_region.country_id = region.country_id
    if region.is_visible is not None:
        db_region.is_visible = region.is_visible

    db.commit()
    db.refresh(db_region)

    return RegionResponse(
        id=db_region.id,
        name=db_region.name,
        country_id=db_region.country_id,
        is_visible=db_region.is_visible,
        created_at=db_region.created_at,
        municipality_count=len(db_region.municipalities)
    )


@router.delete("/{region_id}", response_model=MessageResponse)
def delete_region(
    region_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Delete a region (admin only)."""
    db_region = db.query(Region).filter(Region.id == region_id).first()
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region with id {region_id} not found"
        )

    db.delete(db_region)
    db.commit()

    return MessageResponse(message=f"Region '{db_region.name}' deleted successfully")
