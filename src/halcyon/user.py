"""
Lightweight user model for the Halcyon Matrix client library.

Provides a structured representation of Matrix user identity that can
be attached to events when room member data is available.
"""

from pydantic import BaseModel, PrivateAttr
from typing import Optional, Dict, Any
from halcyon.security import get_nested_config


class User(BaseModel):
    """Matrix user identity.

    Constructed from room member data when available. Avoids extra
    network requests by reusing data already present in the room cache.
    """
    model_config = get_nested_config()

    id: Optional[str] = None
    displayname: Optional[str] = None
    avatar_url: Optional[str] = None
    membership: Optional[str] = None

    def __bool__(self):
        return self.id is not None

    def __str__(self):
        return self.displayname or self.id or ""
