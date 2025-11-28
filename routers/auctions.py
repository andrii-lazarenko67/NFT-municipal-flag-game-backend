"""
Auctions API Router.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Auction, Bid, Flag, User, FlagOwnership, AuctionStatus, OwnershipType
from schemas import (
    AuctionCreate, AuctionResponse, AuctionDetailResponse,
    BidCreate, BidResponse, FlagResponse, UserResponse, MessageResponse
)

router = APIRouter(tags=["Auctions"])


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


def build_flag_response(flag: Flag) -> FlagResponse:
    """Build flag response."""
    return FlagResponse(
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
    )


def build_user_response(user: User) -> UserResponse:
    """Build user response."""
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


@router.get("", response_model=List[AuctionResponse])
def get_auctions(
    active_only: bool = True,
    flag_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all auctions."""
    query = db.query(Auction)

    if active_only:
        query = query.filter(Auction.status == AuctionStatus.ACTIVE)
    if flag_id:
        query = query.filter(Auction.flag_id == flag_id)

    auctions = query.order_by(Auction.ends_at).all()

    result = []
    for auction in auctions:
        result.append(AuctionResponse(
            id=auction.id,
            flag_id=auction.flag_id,
            seller_id=auction.seller_id,
            starting_price=auction.starting_price,
            current_highest_bid=auction.current_highest_bid,
            highest_bidder_id=auction.highest_bidder_id,
            status=auction.status,
            ends_at=auction.ends_at,
            created_at=auction.created_at,
            flag=build_flag_response(auction.flag),
            seller=build_user_response(auction.seller),
            bid_count=len(auction.bids)
        ))

    return result


@router.get("/{auction_id}", response_model=AuctionDetailResponse)
def get_auction(
    auction_id: int,
    db: Session = Depends(get_db)
):
    """Get auction details with bid history."""
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Auction with id {auction_id} not found"
        )

    # Build bids list
    bids_data = []
    for bid in sorted(auction.bids, key=lambda b: b.created_at, reverse=True):
        bids_data.append(BidResponse(
            id=bid.id,
            auction_id=bid.auction_id,
            bidder_id=bid.bidder_id,
            amount=bid.amount,
            created_at=bid.created_at,
            bidder=build_user_response(bid.bidder)
        ))

    highest_bidder = None
    if auction.highest_bidder:
        highest_bidder = build_user_response(auction.highest_bidder)

    return AuctionDetailResponse(
        id=auction.id,
        flag_id=auction.flag_id,
        seller_id=auction.seller_id,
        starting_price=auction.starting_price,
        current_highest_bid=auction.current_highest_bid,
        highest_bidder_id=auction.highest_bidder_id,
        status=auction.status,
        ends_at=auction.ends_at,
        created_at=auction.created_at,
        flag=build_flag_response(auction.flag),
        seller=build_user_response(auction.seller),
        bid_count=len(bids_data),
        bids=bids_data,
        highest_bidder=highest_bidder
    )


@router.post("", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED)
def create_auction(
    auction_data: AuctionCreate,
    db: Session = Depends(get_db)
):
    """Create a new auction."""
    # Verify flag exists
    flag = db.query(Flag).filter(Flag.id == auction_data.flag_id).first()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flag with id {auction_data.flag_id} not found"
        )

    # Get seller
    seller = get_or_create_user(db, auction_data.wallet_address)

    # Verify seller owns the flag
    ownership = db.query(FlagOwnership).filter(
        FlagOwnership.flag_id == auction_data.flag_id,
        FlagOwnership.user_id == seller.id
    ).first()
    if not ownership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must own this flag to create an auction"
        )

    # Check if there's already an active auction for this flag
    existing = db.query(Auction).filter(
        Auction.flag_id == auction_data.flag_id,
        Auction.status == AuctionStatus.ACTIVE
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already an active auction for this flag"
        )

    # Create auction
    ends_at = datetime.utcnow() + timedelta(hours=auction_data.duration_hours)
    auction = Auction(
        flag_id=auction_data.flag_id,
        seller_id=seller.id,
        starting_price=auction_data.starting_price,
        ends_at=ends_at
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    return AuctionResponse(
        id=auction.id,
        flag_id=auction.flag_id,
        seller_id=auction.seller_id,
        starting_price=auction.starting_price,
        current_highest_bid=auction.current_highest_bid,
        highest_bidder_id=auction.highest_bidder_id,
        status=auction.status,
        ends_at=auction.ends_at,
        created_at=auction.created_at,
        flag=build_flag_response(flag),
        seller=build_user_response(seller),
        bid_count=0
    )


@router.post("/{auction_id}/bid", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
def place_bid(
    auction_id: int,
    bid_data: BidCreate,
    db: Session = Depends(get_db)
):
    """Place a bid on an auction."""
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Auction with id {auction_id} not found"
        )

    # Check auction is active
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not active"
        )

    # Check auction hasn't ended
    if datetime.utcnow() > auction.ends_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has ended"
        )

    # Get bidder
    bidder = get_or_create_user(db, bid_data.wallet_address)

    # Can't bid on own auction
    if bidder.id == auction.seller_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot bid on your own auction"
        )

    # Check bid is higher than current highest
    min_bid = auction.current_highest_bid or auction.starting_price
    if bid_data.amount <= min_bid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid must be higher than {min_bid}"
        )

    # Create bid
    bid = Bid(
        auction_id=auction_id,
        bidder_id=bidder.id,
        amount=bid_data.amount
    )
    db.add(bid)

    # Update auction
    auction.current_highest_bid = bid_data.amount
    auction.highest_bidder_id = bidder.id

    db.commit()
    db.refresh(bid)

    return BidResponse(
        id=bid.id,
        auction_id=bid.auction_id,
        bidder_id=bid.bidder_id,
        amount=bid.amount,
        created_at=bid.created_at,
        bidder=build_user_response(bidder)
    )


@router.post("/{auction_id}/close", response_model=AuctionResponse)
def close_auction(
    auction_id: int,
    db: Session = Depends(get_db)
):
    """Close an auction (can be called by anyone after end time)."""
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Auction with id {auction_id} not found"
        )

    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not active"
        )

    # Check if auction time has ended
    if datetime.utcnow() < auction.ends_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has not ended yet"
        )

    # Close the auction
    auction.status = AuctionStatus.CLOSED

    # If there was a winner, transfer ownership (off-chain record)
    if auction.highest_bidder_id:
        # Award reputation to winner
        winner = db.query(User).filter(User.id == auction.highest_bidder_id).first()
        if winner:
            winner.reputation_score += 15

    db.commit()
    db.refresh(auction)

    return AuctionResponse(
        id=auction.id,
        flag_id=auction.flag_id,
        seller_id=auction.seller_id,
        starting_price=auction.starting_price,
        current_highest_bid=auction.current_highest_bid,
        highest_bidder_id=auction.highest_bidder_id,
        status=auction.status,
        ends_at=auction.ends_at,
        created_at=auction.created_at,
        flag=build_flag_response(auction.flag),
        seller=build_user_response(auction.seller),
        bid_count=len(auction.bids)
    )


@router.post("/{auction_id}/cancel", response_model=MessageResponse)
def cancel_auction(
    auction_id: int,
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Cancel an auction (only seller can cancel if no bids)."""
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Auction with id {auction_id} not found"
        )

    # Get user
    wallet = wallet_address.lower()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user or user.id != auction.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can cancel the auction"
        )

    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not active"
        )

    # Can only cancel if no bids
    if auction.current_highest_bid is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel auction with existing bids"
        )

    auction.status = AuctionStatus.CANCELLED
    db.commit()

    return MessageResponse(message="Auction cancelled successfully")
