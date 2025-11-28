"""
SQLAlchemy models for the Municipal Flag NFT Game.
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Enum, Text, UniqueConstraint, Numeric
)
from sqlalchemy.orm import relationship
from database import Base


# =============================================================================
# ENUMS
# =============================================================================

class FlagCategory(PyEnum):
    """Flag category types with discount levels."""
    STANDARD = "standard"
    PLUS = "plus"
    PREMIUM = "premium"


class NFTStatus(PyEnum):
    """Status of an NFT unit."""
    AVAILABLE = "available"
    CLAIMED = "claimed"
    PURCHASED = "purchased"


class OwnershipType(PyEnum):
    """Type of NFT ownership."""
    FIRST = "first"
    SECOND = "second"


class AuctionStatus(PyEnum):
    """Auction status."""
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# =============================================================================
# GEOGRAPHIC MODELS
# =============================================================================

class Country(Base):
    """Country model - top level of geographic hierarchy."""
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(3), nullable=False, unique=True)  # ISO 3166-1 alpha-3
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    regions = relationship("Region", back_populates="country", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Country(id={self.id}, name='{self.name}', code='{self.code}')>"


class Region(Base):
    """Region model - second level of geographic hierarchy."""
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    country = relationship("Country", back_populates="regions")
    municipalities = relationship("Municipality", back_populates="region", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Region(id={self.id}, name='{self.name}')>"


class Municipality(Base):
    """Municipality model - third level of geographic hierarchy."""
    __tablename__ = "municipalities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="municipalities")
    flags = relationship("Flag", back_populates="municipality", cascade="all, delete-orphan")

    @property
    def coordinates(self) -> str:
        """Return formatted coordinates."""
        return f"{self.latitude:.6f}, {self.longitude:.6f}"

    def __repr__(self):
        return f"<Municipality(id={self.id}, name='{self.name}')>"


# =============================================================================
# FLAG / NFT MODELS
# =============================================================================

class Flag(Base):
    """Flag NFT model - represents a municipal flag with pair logic."""
    __tablename__ = "flags"

    id = Column(Integer, primary_key=True, index=True)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)

    # Name is the coordinates of a location in the municipality
    name = Column(String(100), nullable=False)
    location_type = Column(String(50), nullable=False)  # fire station, bakery, etc.

    # Category determines discounts
    category = Column(Enum(FlagCategory), default=FlagCategory.STANDARD)

    # IPFS storage
    image_ipfs_hash = Column(String(100), nullable=True)
    metadata_ipfs_hash = Column(String(100), nullable=True)

    # Blockchain data
    token_id = Column(Integer, nullable=True)  # Assigned after minting
    price = Column(Numeric(18, 8), default=0.01)  # Price in MATIC

    # Pair status
    first_nft_status = Column(Enum(NFTStatus), default=NFTStatus.AVAILABLE)
    second_nft_status = Column(Enum(NFTStatus), default=NFTStatus.AVAILABLE)
    is_pair_complete = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    municipality = relationship("Municipality", back_populates="flags")
    interests = relationship("FlagInterest", back_populates="flag", cascade="all, delete-orphan")
    ownerships = relationship("FlagOwnership", back_populates="flag", cascade="all, delete-orphan")
    auctions = relationship("Auction", back_populates="flag", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Flag(id={self.id}, name='{self.name}', category={self.category.value})>"


# =============================================================================
# USER MODELS
# =============================================================================

class User(Base):
    """User model - identified by wallet address."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=True)
    reputation_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interests = relationship("FlagInterest", back_populates="user", cascade="all, delete-orphan")
    ownerships = relationship("FlagOwnership", back_populates="user", cascade="all, delete-orphan")

    # Social connections
    followers = relationship(
        "UserConnection",
        foreign_keys="UserConnection.following_id",
        back_populates="following",
        cascade="all, delete-orphan"
    )
    following = relationship(
        "UserConnection",
        foreign_keys="UserConnection.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )

    # Auctions
    auctions_created = relationship(
        "Auction",
        foreign_keys="Auction.seller_id",
        back_populates="seller"
    )
    bids = relationship("Bid", back_populates="bidder", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, wallet='{self.wallet_address[:10]}...')>"


# =============================================================================
# INTERACTION MODELS
# =============================================================================

class FlagInterest(Base):
    """Tracks user interest in a flag (for first NFT claim)."""
    __tablename__ = "flag_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    flag_id = Column(Integer, ForeignKey("flags.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="interests")
    flag = relationship("Flag", back_populates="interests")

    # Unique constraint - user can only express interest once per flag
    __table_args__ = (
        UniqueConstraint("user_id", "flag_id", name="unique_user_flag_interest"),
    )

    def __repr__(self):
        return f"<FlagInterest(user_id={self.user_id}, flag_id={self.flag_id})>"


class FlagOwnership(Base):
    """Tracks NFT ownership."""
    __tablename__ = "flag_ownerships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    flag_id = Column(Integer, ForeignKey("flags.id"), nullable=False)
    ownership_type = Column(Enum(OwnershipType), nullable=False)
    transaction_hash = Column(String(66), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ownerships")
    flag = relationship("Flag", back_populates="ownerships")

    def __repr__(self):
        return f"<FlagOwnership(user_id={self.user_id}, flag_id={self.flag_id}, type={self.ownership_type.value})>"


class UserConnection(Base):
    """Social connection between users (follow relationship)."""
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")

    # Unique constraint - can only follow once
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="unique_follow"),
    )

    def __repr__(self):
        return f"<UserConnection(follower={self.follower_id}, following={self.following_id})>"


# =============================================================================
# AUCTION MODELS
# =============================================================================

class Auction(Base):
    """Off-chain auction for flags."""
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(Integer, ForeignKey("flags.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    starting_price = Column(Numeric(18, 8), nullable=False)
    current_highest_bid = Column(Numeric(18, 8), nullable=True)
    highest_bidder_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = Column(Enum(AuctionStatus), default=AuctionStatus.ACTIVE)
    ends_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    flag = relationship("Flag", back_populates="auctions")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="auctions_created")
    highest_bidder = relationship("User", foreign_keys=[highest_bidder_id])
    bids = relationship("Bid", back_populates="auction", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Auction(id={self.id}, flag_id={self.flag_id}, status={self.status.value})>"


class Bid(Base):
    """Bid in an auction."""
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    bidder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    auction = relationship("Auction", back_populates="bids")
    bidder = relationship("User", back_populates="bids")

    def __repr__(self):
        return f"<Bid(auction_id={self.auction_id}, amount={self.amount})>"
