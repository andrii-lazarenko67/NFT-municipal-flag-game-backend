"""
Users API Router.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserConnection, FlagOwnership, FlagInterest
from schemas import (
    UserCreate, UserUpdate, UserResponse, UserDetailResponse,
    FollowCreate, ConnectionResponse, FlagOwnershipResponse,
    FlagInterestResponse, MessageResponse
)

router = APIRouter(tags=["Users"])


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


def build_user_response(user: User) -> UserResponse:
    """Build user response with counts."""
    return UserResponse(
        id=user.id,
        wallet_address=user.wallet_address,
        username=user.username,
        reputation_score=user.reputation_score,
        created_at=user.created_at,
        flags_owned=len(user.ownerships),
        followers_count=len(user.followers),
        following_count=len(user.following)
    )


@router.get("/{wallet_address}", response_model=UserResponse)
def get_user(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Get user by wallet address."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with wallet {wallet_address} not found"
        )

    return build_user_response(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_or_get_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user or get existing one."""
    user = get_or_create_user(db, user_data.wallet_address)

    if user_data.username:
        user.username = user_data.username
        db.commit()
        db.refresh(user)

    return build_user_response(user)


@router.put("/{wallet_address}", response_model=UserResponse)
def update_user(
    wallet_address: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with wallet {wallet_address} not found"
        )

    if user_data.username is not None:
        user.username = user_data.username

    db.commit()
    db.refresh(user)

    return build_user_response(user)


@router.get("/{wallet_address}/flags", response_model=List[FlagOwnershipResponse])
def get_user_flags(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Get all flags owned by a user."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with wallet {wallet_address} not found"
        )

    result = []
    for ownership in user.ownerships:
        result.append(FlagOwnershipResponse(
            id=ownership.id,
            user_id=ownership.user_id,
            flag_id=ownership.flag_id,
            ownership_type=ownership.ownership_type,
            transaction_hash=ownership.transaction_hash,
            created_at=ownership.created_at
        ))

    return result


@router.get("/{wallet_address}/interests", response_model=List[FlagInterestResponse])
def get_user_interests(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Get all flag interests for a user."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with wallet {wallet_address} not found"
        )

    result = []
    for interest in user.interests:
        result.append(FlagInterestResponse(
            id=interest.id,
            user_id=interest.user_id,
            flag_id=interest.flag_id,
            created_at=interest.created_at
        ))

    return result


# =============================================================================
# SOCIAL CONNECTIONS
# =============================================================================

@router.post("/{wallet_address}/follow", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
def follow_user(
    wallet_address: str,
    follow_data: FollowCreate,
    db: Session = Depends(get_db)
):
    """Follow another user."""
    follower_wallet = wallet_address.lower()
    following_wallet = follow_data.target_wallet.lower()

    if follower_wallet == following_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself"
        )

    # Get or create both users
    follower = get_or_create_user(db, follower_wallet)
    following = get_or_create_user(db, following_wallet)

    # Check if already following
    existing = db.query(UserConnection).filter(
        UserConnection.follower_id == follower.id,
        UserConnection.following_id == following.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already following this user"
        )

    # Create connection
    connection = UserConnection(
        follower_id=follower.id,
        following_id=following.id
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return ConnectionResponse(
        id=connection.id,
        follower_id=connection.follower_id,
        following_id=connection.following_id,
        created_at=connection.created_at,
        follower=build_user_response(follower),
        following=build_user_response(following)
    )


@router.delete("/{wallet_address}/follow/{target_wallet}", response_model=MessageResponse)
def unfollow_user(
    wallet_address: str,
    target_wallet: str,
    db: Session = Depends(get_db)
):
    """Unfollow a user."""
    follower_wallet = wallet_address.lower()
    following_wallet = target_wallet.lower()

    follower = db.query(User).filter(User.wallet_address == follower_wallet).first()
    following = db.query(User).filter(User.wallet_address == following_wallet).first()

    if not follower or not following:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    connection = db.query(UserConnection).filter(
        UserConnection.follower_id == follower.id,
        UserConnection.following_id == following.id
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    db.delete(connection)
    db.commit()

    return MessageResponse(message="Unfollowed successfully")


@router.get("/{wallet_address}/followers", response_model=List[UserResponse])
def get_followers(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Get all followers of a user."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with wallet {wallet_address} not found"
        )

    result = []
    for connection in user.followers:
        follower = connection.follower
        result.append(build_user_response(follower))

    return result


@router.get("/{wallet_address}/following", response_model=List[UserResponse])
def get_following(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Get all users that a user is following."""
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with wallet {wallet_address} not found"
        )

    result = []
    for connection in user.following:
        following = connection.following
        result.append(build_user_response(following))

    return result
