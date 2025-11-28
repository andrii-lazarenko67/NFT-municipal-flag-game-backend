"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from models import FlagCategory, NFTStatus, OwnershipType, AuctionStatus


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        from_attributes = True


# =============================================================================
# COUNTRY SCHEMAS
# =============================================================================

class CountryCreate(BaseModel):
    """Schema for creating a country."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=2, max_length=3)
    is_visible: bool = True


class CountryUpdate(BaseModel):
    """Schema for updating a country."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=3)
    is_visible: Optional[bool] = None


class CountryResponse(BaseSchema):
    """Schema for country response."""
    id: int
    name: str
    code: str
    is_visible: bool
    created_at: datetime
    region_count: Optional[int] = 0


class CountryDetailResponse(CountryResponse):
    """Schema for country detail with regions."""
    regions: List["RegionResponse"] = []


# =============================================================================
# REGION SCHEMAS
# =============================================================================

class RegionCreate(BaseModel):
    """Schema for creating a region."""
    name: str = Field(..., min_length=1, max_length=100)
    country_id: int
    is_visible: bool = True


class RegionUpdate(BaseModel):
    """Schema for updating a region."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    country_id: Optional[int] = None
    is_visible: Optional[bool] = None


class RegionResponse(BaseSchema):
    """Schema for region response."""
    id: int
    name: str
    country_id: int
    is_visible: bool
    created_at: datetime
    municipality_count: Optional[int] = 0


class RegionDetailResponse(RegionResponse):
    """Schema for region detail with country and municipalities."""
    country: Optional[CountryResponse] = None
    municipalities: List["MunicipalityResponse"] = []


# =============================================================================
# MUNICIPALITY SCHEMAS
# =============================================================================

class MunicipalityCreate(BaseModel):
    """Schema for creating a municipality."""
    name: str = Field(..., min_length=1, max_length=100)
    region_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_visible: bool = True


class MunicipalityUpdate(BaseModel):
    """Schema for updating a municipality."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    region_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_visible: Optional[bool] = None


class MunicipalityResponse(BaseSchema):
    """Schema for municipality response."""
    id: int
    name: str
    region_id: int
    latitude: float
    longitude: float
    coordinates: str
    is_visible: bool
    created_at: datetime
    flag_count: Optional[int] = 0


class MunicipalityDetailResponse(MunicipalityResponse):
    """Schema for municipality detail with region and flags."""
    region: Optional[RegionResponse] = None
    flags: List["FlagResponse"] = []


# =============================================================================
# FLAG SCHEMAS
# =============================================================================

class FlagCreate(BaseModel):
    """Schema for creating a flag."""
    municipality_id: int
    name: str = Field(..., min_length=1, max_length=100)
    location_type: str = Field(..., min_length=1, max_length=50)
    category: FlagCategory = FlagCategory.STANDARD
    image_ipfs_hash: Optional[str] = None
    metadata_ipfs_hash: Optional[str] = None
    price: Decimal = Decimal("0.01")


class FlagUpdate(BaseModel):
    """Schema for updating a flag."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location_type: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[FlagCategory] = None
    image_ipfs_hash: Optional[str] = None
    metadata_ipfs_hash: Optional[str] = None
    price: Optional[Decimal] = None


class FlagResponse(BaseSchema):
    """Schema for flag response."""
    id: int
    municipality_id: int
    name: str
    location_type: str
    category: FlagCategory
    image_ipfs_hash: Optional[str]
    metadata_ipfs_hash: Optional[str]
    token_id: Optional[int]
    price: Decimal
    first_nft_status: NFTStatus
    second_nft_status: NFTStatus
    is_pair_complete: bool
    created_at: datetime
    interest_count: Optional[int] = 0


class FlagDetailResponse(FlagResponse):
    """Schema for flag detail with municipality and interests."""
    municipality: Optional[MunicipalityResponse] = None
    interests: List["FlagInterestResponse"] = []
    ownerships: List["FlagOwnershipResponse"] = []


# =============================================================================
# USER SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    """Schema for creating a user."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    username: Optional[str] = Field(None, min_length=1, max_length=50)

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=1, max_length=50)


class UserResponse(BaseSchema):
    """Schema for user response."""
    id: int
    wallet_address: str
    username: Optional[str]
    reputation_score: int
    created_at: datetime
    flags_owned: Optional[int] = 0
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0


class UserDetailResponse(UserResponse):
    """Schema for user detail with owned flags and interests."""
    ownerships: List["FlagOwnershipResponse"] = []
    interests: List["FlagInterestResponse"] = []


# =============================================================================
# INTERACTION SCHEMAS
# =============================================================================

class FlagInterestCreate(BaseModel):
    """Schema for creating a flag interest."""
    wallet_address: str = Field(..., min_length=42, max_length=42)

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        return v.lower()


class FlagInterestResponse(BaseSchema):
    """Schema for flag interest response."""
    id: int
    user_id: int
    flag_id: int
    created_at: datetime
    user: Optional[UserResponse] = None


class FlagOwnershipResponse(BaseSchema):
    """Schema for flag ownership response."""
    id: int
    user_id: int
    flag_id: int
    ownership_type: OwnershipType
    transaction_hash: Optional[str]
    created_at: datetime
    user: Optional[UserResponse] = None


class FlagOwnershipCreate(BaseModel):
    """Schema for recording flag ownership."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    ownership_type: OwnershipType
    transaction_hash: Optional[str] = None

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        return v.lower()


# =============================================================================
# SOCIAL SCHEMAS
# =============================================================================

class FollowCreate(BaseModel):
    """Schema for following a user."""
    target_wallet: str = Field(..., min_length=42, max_length=42)

    @field_validator("target_wallet")
    @classmethod
    def validate_wallet(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        return v.lower()


class ConnectionResponse(BaseSchema):
    """Schema for connection response."""
    id: int
    follower_id: int
    following_id: int
    created_at: datetime
    follower: Optional[UserResponse] = None
    following: Optional[UserResponse] = None


# =============================================================================
# AUCTION SCHEMAS
# =============================================================================

class AuctionCreate(BaseModel):
    """Schema for creating an auction."""
    flag_id: int
    wallet_address: str = Field(..., min_length=42, max_length=42)
    starting_price: Decimal = Field(..., gt=0)
    duration_hours: int = Field(..., ge=1, le=168)  # 1 hour to 7 days

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        return v.lower()


class AuctionResponse(BaseSchema):
    """Schema for auction response."""
    id: int
    flag_id: int
    seller_id: int
    starting_price: Decimal
    current_highest_bid: Optional[Decimal]
    highest_bidder_id: Optional[int]
    status: AuctionStatus
    ends_at: datetime
    created_at: datetime
    flag: Optional[FlagResponse] = None
    seller: Optional[UserResponse] = None
    bid_count: Optional[int] = 0


class AuctionDetailResponse(AuctionResponse):
    """Schema for auction detail with bids."""
    bids: List["BidResponse"] = []
    highest_bidder: Optional[UserResponse] = None


class BidCreate(BaseModel):
    """Schema for placing a bid."""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    amount: Decimal = Field(..., gt=0)

    @field_validator("wallet_address")
    @classmethod
    def validate_wallet(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        return v.lower()


class BidResponse(BaseSchema):
    """Schema for bid response."""
    id: int
    auction_id: int
    bidder_id: int
    amount: Decimal
    created_at: datetime
    bidder: Optional[UserResponse] = None


# =============================================================================
# RANKING SCHEMAS
# =============================================================================

class UserRankingResponse(BaseModel):
    """Schema for user ranking."""
    rank: int
    user: UserResponse
    score: int


class FlagRankingResponse(BaseModel):
    """Schema for flag ranking."""
    rank: int
    flag: FlagResponse
    interest_count: int


# =============================================================================
# ADMIN SCHEMAS
# =============================================================================

class AdminStatsResponse(BaseModel):
    """Schema for admin statistics."""
    total_countries: int
    total_regions: int
    total_municipalities: int
    total_flags: int
    total_users: int
    total_interests: int
    total_ownerships: int
    total_auctions: int
    active_auctions: int
    completed_pairs: int


# =============================================================================
# COMMON SCHEMAS
# =============================================================================

class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    success: bool = False


# Update forward references
CountryDetailResponse.model_rebuild()
RegionDetailResponse.model_rebuild()
MunicipalityDetailResponse.model_rebuild()
FlagDetailResponse.model_rebuild()
UserDetailResponse.model_rebuild()
AuctionDetailResponse.model_rebuild()
