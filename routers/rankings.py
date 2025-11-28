"""
Rankings API Router.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, Flag, FlagOwnership, FlagInterest
from schemas import UserRankingResponse, FlagRankingResponse, UserResponse, FlagResponse

router = APIRouter(tags=["Rankings"])


@router.get("/users", response_model=List[UserRankingResponse])
def get_user_rankings(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top users by reputation score."""
    users = db.query(User).order_by(User.reputation_score.desc()).limit(limit).all()

    result = []
    for rank, user in enumerate(users, start=1):
        result.append(UserRankingResponse(
            rank=rank,
            user=UserResponse(
                id=user.id,
                wallet_address=user.wallet_address,
                username=user.username,
                reputation_score=user.reputation_score,
                created_at=user.created_at,
                flags_owned=len(user.ownerships),
                followers_count=len(user.followers),
                following_count=len(user.following)
            ),
            score=user.reputation_score
        ))

    return result


@router.get("/collectors", response_model=List[UserRankingResponse])
def get_collector_rankings(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top users by number of flags owned."""
    # Query users with ownership count
    user_ownership_counts = db.query(
        User,
        func.count(FlagOwnership.id).label('ownership_count')
    ).outerjoin(FlagOwnership).group_by(User.id).order_by(
        func.count(FlagOwnership.id).desc()
    ).limit(limit).all()

    result = []
    for rank, (user, ownership_count) in enumerate(user_ownership_counts, start=1):
        if ownership_count > 0:  # Only include users with at least one flag
            result.append(UserRankingResponse(
                rank=rank,
                user=UserResponse(
                    id=user.id,
                    wallet_address=user.wallet_address,
                    username=user.username,
                    reputation_score=user.reputation_score,
                    created_at=user.created_at,
                    flags_owned=ownership_count,
                    followers_count=len(user.followers),
                    following_count=len(user.following)
                ),
                score=ownership_count
            ))

    return result


@router.get("/flags", response_model=List[FlagRankingResponse])
def get_popular_flags(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most popular flags by interest count."""
    # Query flags with interest count
    flag_interest_counts = db.query(
        Flag,
        func.count(FlagInterest.id).label('interest_count')
    ).outerjoin(FlagInterest).group_by(Flag.id).order_by(
        func.count(FlagInterest.id).desc()
    ).limit(limit).all()

    result = []
    for rank, (flag, interest_count) in enumerate(flag_interest_counts, start=1):
        result.append(FlagRankingResponse(
            rank=rank,
            flag=FlagResponse(
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
                interest_count=interest_count
            ),
            interest_count=interest_count
        ))

    return result


@router.get("/active-collectors", response_model=List[UserRankingResponse])
def get_active_collectors(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get users who are most active (interests + ownerships + connections)."""
    users = db.query(User).all()

    # Calculate activity score for each user
    user_scores = []
    for user in users:
        activity_score = (
            len(user.interests) * 1 +  # 1 point per interest
            len(user.ownerships) * 5 +  # 5 points per ownership
            len(user.followers) * 2 +  # 2 points per follower
            len(user.following) * 1  # 1 point per following
        )
        if activity_score > 0:
            user_scores.append((user, activity_score))

    # Sort by activity score
    user_scores.sort(key=lambda x: x[1], reverse=True)

    result = []
    for rank, (user, score) in enumerate(user_scores[:limit], start=1):
        result.append(UserRankingResponse(
            rank=rank,
            user=UserResponse(
                id=user.id,
                wallet_address=user.wallet_address,
                username=user.username,
                reputation_score=user.reputation_score,
                created_at=user.created_at,
                flags_owned=len(user.ownerships),
                followers_count=len(user.followers),
                following_count=len(user.following)
            ),
            score=score
        ))

    return result
