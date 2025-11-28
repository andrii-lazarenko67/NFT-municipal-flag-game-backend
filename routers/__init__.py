"""
API Routers for the Municipal Flag NFT Game.
"""
from .countries import router as countries_router
from .regions import router as regions_router
from .municipalities import router as municipalities_router
from .flags import router as flags_router
from .users import router as users_router
from .auctions import router as auctions_router
from .rankings import router as rankings_router
from .admin import router as admin_router

__all__ = [
    "countries_router",
    "regions_router",
    "municipalities_router",
    "flags_router",
    "users_router",
    "auctions_router",
    "rankings_router",
    "admin_router",
]
