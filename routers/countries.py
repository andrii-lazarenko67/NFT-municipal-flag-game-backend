"""
Countries API Router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Country, Region
from schemas import (
    CountryCreate, CountryUpdate, CountryResponse,
    CountryDetailResponse, MessageResponse
)
from config import settings

router = APIRouter(tags=["Countries"])


def verify_admin(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key for protected endpoints."""
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin API key"
        )
    return True


@router.get("", response_model=List[CountryResponse])
def get_countries(
    visible_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all countries."""
    query = db.query(Country)
    if visible_only:
        query = query.filter(Country.is_visible == True)

    countries = query.order_by(Country.name).all()

    # Add region count
    result = []
    for country in countries:
        country_dict = {
            "id": country.id,
            "name": country.name,
            "code": country.code,
            "is_visible": country.is_visible,
            "created_at": country.created_at,
            "region_count": len([r for r in country.regions if r.is_visible or not visible_only])
        }
        result.append(CountryResponse(**country_dict))

    return result


@router.get("/{country_id}", response_model=CountryDetailResponse)
def get_country(
    country_id: int,
    db: Session = Depends(get_db)
):
    """Get a single country with its regions."""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with id {country_id} not found"
        )

    # Build response with regions
    regions_data = []
    for region in country.regions:
        if region.is_visible:
            regions_data.append({
                "id": region.id,
                "name": region.name,
                "country_id": region.country_id,
                "is_visible": region.is_visible,
                "created_at": region.created_at,
                "municipality_count": len([m for m in region.municipalities if m.is_visible])
            })

    return CountryDetailResponse(
        id=country.id,
        name=country.name,
        code=country.code,
        is_visible=country.is_visible,
        created_at=country.created_at,
        region_count=len(regions_data),
        regions=regions_data
    )


@router.post("", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
def create_country(
    country: CountryCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Create a new country (admin only)."""
    # Check if code already exists
    existing = db.query(Country).filter(Country.code == country.code.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Country with code {country.code} already exists"
        )

    db_country = Country(
        name=country.name,
        code=country.code.upper(),
        is_visible=country.is_visible
    )
    db.add(db_country)
    db.commit()
    db.refresh(db_country)

    return CountryResponse(
        id=db_country.id,
        name=db_country.name,
        code=db_country.code,
        is_visible=db_country.is_visible,
        created_at=db_country.created_at,
        region_count=0
    )


@router.put("/{country_id}", response_model=CountryResponse)
def update_country(
    country_id: int,
    country: CountryUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Update a country (admin only)."""
    db_country = db.query(Country).filter(Country.id == country_id).first()
    if not db_country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with id {country_id} not found"
        )

    # Update fields if provided
    if country.name is not None:
        db_country.name = country.name
    if country.code is not None:
        # Check if new code is unique
        existing = db.query(Country).filter(
            Country.code == country.code.upper(),
            Country.id != country_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Country with code {country.code} already exists"
            )
        db_country.code = country.code.upper()
    if country.is_visible is not None:
        db_country.is_visible = country.is_visible

    db.commit()
    db.refresh(db_country)

    return CountryResponse(
        id=db_country.id,
        name=db_country.name,
        code=db_country.code,
        is_visible=db_country.is_visible,
        created_at=db_country.created_at,
        region_count=len(db_country.regions)
    )


@router.delete("/{country_id}", response_model=MessageResponse)
def delete_country(
    country_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Delete a country (admin only)."""
    db_country = db.query(Country).filter(Country.id == country_id).first()
    if not db_country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with id {country_id} not found"
        )

    db.delete(db_country)
    db.commit()

    return MessageResponse(message=f"Country '{db_country.name}' deleted successfully")
