"""
Flags API Router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from database import get_db
from models import Flag, Municipality, User, FlagInterest, FlagOwnership, NFTStatus, OwnershipType
from schemas import (
    FlagCreate, FlagUpdate, FlagResponse, FlagDetailResponse,
    FlagInterestCreate, FlagInterestResponse, FlagOwnershipCreate,
    FlagOwnershipResponse, MunicipalityResponse, UserResponse, MessageResponse
)
from config import settings

router = APIRouter(tags=["Flags"])


def verify_admin(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key for protected endpoints."""
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin API key"
        )
    return True


def get_or_create_user(db: Session, wallet_address: str) -> User:
    """Get existing user or create new one."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        user = User(wallet_address=wallet)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("", response_model=List[FlagResponse])
def get_flags(
    municipality_id: Optional[int] = None,
    category: Optional[str] = None,
    available_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all flags with optional filters."""
    query = db.query(Flag)

    if municipality_id:
        query = query.filter(Flag.municipality_id == municipality_id)
    if category:
        query = query.filter(Flag.category == category)
    if available_only:
        query = query.filter(Flag.is_pair_complete == False)

    flags = query.order_by(Flag.id).all()

    result = []
    for flag in flags:
        result.append(FlagResponse(
            id=flag.id,
            municipality_id=flag.municipality_id,
            name=flag.name,
            location_type=flag.location_type,
            category=flag.category,
            image_ipfs_hash=flag.image_ipfs_hash,
            metadata_ipfs_hash=flag.metadata_ipfs_hash,
            token_id=flag.token_id,
            price=flag.price,
            first_nft_status=flag.first_nft_status,
            second_nft_status=flag.second_nft_status,
            is_pair_complete=flag.is_pair_complete,
            created_at=flag.created_at,
            interest_count=len(flag.interests)
        ))

    return result


@router.get("/{flag_id}", response_model=FlagDetailResponse)
def get_flag(
    flag_id: int,
    db: Session = Depends(get_db)
):
    """Get a single flag with all details."""
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    # Build municipality response
    municipality_data = MunicipalityResponse(
        id=flag.municipality.id,
        name=flag.municipality.name,
        region_id=flag.municipality.region_id,
        latitude=flag.municipality.latitude,
        longitude=flag.municipality.longitude,
        coordinates=flag.municipality.coordinates,
        is_visible=flag.municipality.is_visible,
        created_at=flag.municipality.created_at,
        flag_count=len(flag.municipality.flags)
    )

    # Build interests list
    interests_data = []
    for interest in flag.interests:
        user = interest.user
        interests_data.append(FlagInterestResponse(
            id=interest.id,
            user_id=interest.user_id,
            flag_id=interest.flag_id,
            created_at=interest.created_at,
            user=UserResponse(
                id=user.id,
                wallet_address=user.wallet_address,
                username=user.username,
                reputation_score=user.reputation_score,
                created_at=user.created_at
            )
        ))

    # Build ownerships list
    ownerships_data = []
    for ownership in flag.ownerships:
        user = ownership.user
        ownerships_data.append(FlagOwnershipResponse(
            id=ownership.id,
            user_id=ownership.user_id,
            flag_id=ownership.flag_id,
            ownership_type=ownership.ownership_type,
            transaction_hash=ownership.transaction_hash,
            created_at=ownership.created_at,
            user=UserResponse(
                id=user.id,
                wallet_address=user.wallet_address,
                username=user.username,
                reputation_score=user.reputation_score,
                created_at=user.created_at
            )
        ))

    return FlagDetailResponse(
        id=flag.id,
        municipality_id=flag.municipality_id,
        name=flag.name,
        location_type=flag.location_type,
        category=flag.category,
        image_ipfs_hash=flag.image_ipfs_hash,
        metadata_ipfs_hash=flag.metadata_ipfs_hash,
        token_id=flag.token_id,
        price=flag.price,
        first_nft_status=flag.first_nft_status,
        second_nft_status=flag.second_nft_status,
        is_pair_complete=flag.is_pair_complete,
        created_at=flag.created_at,
        interest_count=len(interests_data),
        municipality=municipality_data,
        interests=interests_data,
        ownerships=ownerships_data
    )


@router.post("", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
def create_flag(
    flag: FlagCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Create a new flag (admin only)."""
    # Verify municipality exists
    municipality = db.query(Municipality).filter(Municipality.id == flag.municipality_id).first()
    if not municipality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Municipality with id {flag.municipality_id} not found"
        )

    db_flag = Flag(
        municipality_id=flag.municipality_id,
        name=flag.name,
        location_type=flag.location_type,
        category=flag.category,
        image_ipfs_hash=flag.image_ipfs_hash,
        metadata_ipfs_hash=flag.metadata_ipfs_hash,
        price=flag.price
    )
    db.add(db_flag)
    db.commit()
    db.refresh(db_flag)

    return FlagResponse(
        id=db_flag.id,
        municipality_id=db_flag.municipality_id,
        name=db_flag.name,
        location_type=db_flag.location_type,
        category=db_flag.category,
        image_ipfs_hash=db_flag.image_ipfs_hash,
        metadata_ipfs_hash=db_flag.metadata_ipfs_hash,
        token_id=db_flag.token_id,
        price=db_flag.price,
        first_nft_status=db_flag.first_nft_status,
        second_nft_status=db_flag.second_nft_status,
        is_pair_complete=db_flag.is_pair_complete,
        created_at=db_flag.created_at,
        interest_count=0
    )


@router.put("/{flag_id}", response_model=FlagResponse)
def update_flag(
    flag_id: int,
    flag: FlagUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Update a flag (admin only)."""
    db_flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not db_flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    if flag.name is not None:
        db_flag.name = flag.name
    if flag.location_type is not None:
        db_flag.location_type = flag.location_type
    if flag.category is not None:
        db_flag.category = flag.category
    if flag.image_ipfs_hash is not None:
        db_flag.image_ipfs_hash = flag.image_ipfs_hash
    if flag.metadata_ipfs_hash is not None:
        db_flag.metadata_ipfs_hash = flag.metadata_ipfs_hash
    if flag.price is not None:
        db_flag.price = flag.price

    db.commit()
    db.refresh(db_flag)

    return FlagResponse(
        id=db_flag.id,
        municipality_id=db_flag.municipality_id,
        name=db_flag.name,
        location_type=db_flag.location_type,
        category=db_flag.category,
        image_ipfs_hash=db_flag.image_ipfs_hash,
        metadata_ipfs_hash=db_flag.metadata_ipfs_hash,
        token_id=db_flag.token_id,
        price=db_flag.price,
        first_nft_status=db_flag.first_nft_status,
        second_nft_status=db_flag.second_nft_status,
        is_pair_complete=db_flag.is_pair_complete,
        created_at=db_flag.created_at,
        interest_count=len(db_flag.interests)
    )


# =============================================================================
# INTEREST ENDPOINTS
# =============================================================================

@router.post("/{flag_id}/interest", response_model=FlagInterestResponse, status_code=status.HTTP_201_CREATED)
def register_interest(
    flag_id: int,
    interest: FlagInterestCreate,
    db: Session = Depends(get_db)
):
    """Register user interest in a flag (for first NFT)."""
    # Verify flag exists
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    # Get or create user
    user = get_or_create_user(db, interest.wallet_address)

    # Check if already interested
    existing = db.query(FlagInterest).filter(
        FlagInterest.user_id == user.id,
        FlagInterest.flag_id == flag_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already expressed interest in this flag"
        )

    # Create interest
    db_interest = FlagInterest(
        user_id=user.id,
        flag_id=flag_id
    )
    db.add(db_interest)
    db.commit()
    db.refresh(db_interest)

    return FlagInterestResponse(
        id=db_interest.id,
        user_id=db_interest.user_id,
        flag_id=db_interest.flag_id,
        created_at=db_interest.created_at,
        user=UserResponse(
            id=user.id,
            wallet_address=user.wallet_address,
            username=user.username,
            reputation_score=user.reputation_score,
            created_at=user.created_at
        )
    )


@router.get("/{flag_id}/interests", response_model=List[FlagInterestResponse])
def get_flag_interests(
    flag_id: int,
    db: Session = Depends(get_db)
):
    """Get all users interested in a flag."""
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    result = []
    for interest in flag.interests:
        user = interest.user
        result.append(FlagInterestResponse(
            id=interest.id,
            user_id=interest.user_id,
            flag_id=interest.flag_id,
            created_at=interest.created_at,
            user=UserResponse(
                id=user.id,
                wallet_address=user.wallet_address,
                username=user.username,
                reputation_score=user.reputation_score,
                created_at=user.created_at
            )
        ))

    return result


# =============================================================================
# OWNERSHIP ENDPOINTS
# =============================================================================

@router.post("/{flag_id}/claim", response_model=FlagOwnershipResponse, status_code=status.HTTP_201_CREATED)
def claim_first_nft(
    flag_id: int,
    ownership: FlagOwnershipCreate,
    db: Session = Depends(get_db)
):
    """Record first NFT claim (called after blockchain transaction)."""
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    if flag.first_nft_status != NFTStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First NFT already claimed"
        )

    # Get or create user
    user = get_or_create_user(db, ownership.wallet_address)

    # Create ownership record
    db_ownership = FlagOwnership(
        user_id=user.id,
        flag_id=flag_id,
        ownership_type=OwnershipType.FIRST,
        transaction_hash=ownership.transaction_hash
    )
    db.add(db_ownership)

    # Update flag status
    flag.first_nft_status = NFTStatus.CLAIMED

    # Increase user reputation
    user.reputation_score += 10

    db.commit()
    db.refresh(db_ownership)

    return FlagOwnershipResponse(
        id=db_ownership.id,
        user_id=db_ownership.user_id,
        flag_id=db_ownership.flag_id,
        ownership_type=db_ownership.ownership_type,
        transaction_hash=db_ownership.transaction_hash,
        created_at=db_ownership.created_at,
        user=UserResponse(
            id=user.id,
            wallet_address=user.wallet_address,
            username=user.username,
            reputation_score=user.reputation_score,
            created_at=user.created_at
        )
    )


@router.post("/{flag_id}/purchase", response_model=FlagOwnershipResponse, status_code=status.HTTP_201_CREATED)
def purchase_second_nft(
    flag_id: int,
    ownership: FlagOwnershipCreate,
    db: Session = Depends(get_db)
):
    """Record second NFT purchase (called after blockchain transaction)."""
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    if flag.first_nft_status != NFTStatus.CLAIMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First NFT must be claimed before purchasing second"
        )

    if flag.second_nft_status != NFTStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Second NFT already purchased"
        )

    # Get or create user
    user = get_or_create_user(db, ownership.wallet_address)

    # Create ownership record
    db_ownership = FlagOwnership(
        user_id=user.id,
        flag_id=flag_id,
        ownership_type=OwnershipType.SECOND,
        transaction_hash=ownership.transaction_hash
    )
    db.add(db_ownership)

    # Update flag status
    flag.second_nft_status = NFTStatus.PURCHASED
    flag.is_pair_complete = True

    # Increase user reputation
    user.reputation_score += 25

    db.commit()
    db.refresh(db_ownership)

    return FlagOwnershipResponse(
        id=db_ownership.id,
        user_id=db_ownership.user_id,
        flag_id=db_ownership.flag_id,
        ownership_type=db_ownership.ownership_type,
        transaction_hash=db_ownership.transaction_hash,
        created_at=db_ownership.created_at,
        user=UserResponse(
            id=user.id,
            wallet_address=user.wallet_address,
            username=user.username,
            reputation_score=user.reputation_score,
            created_at=user.created_at
        )
    )


@router.get("/{flag_id}/ownerships", response_model=List[FlagOwnershipResponse])
def get_flag_ownerships(
    flag_id: int,
    db: Session = Depends(get_db)
):
    """Get ownership records for a flag."""
    flag = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {flag_id} not found"
        )

    result = []
    for ownership in flag.ownerships:
        user = ownership.user
        result.append(FlagOwnershipResponse(
            id=ownership.id,
            user_id=ownership.user_id,
            flag_id=ownership.flag_id,
            ownership_type=ownership.ownership_type,
            transaction_hash=ownership.transaction_hash,
            created_at=ownership.created_at,
            user=UserResponse(
                id=user.id,
                wallet_address=user.wallet_address,
                username=user.username,
                reputation_score=user.reputation_score,
                created_at=user.created_at
            )
        ))

    return result
