"""Import all ORM models so metadata is complete for Alembic."""

from app.db.base_class import Base

from app.models.category import Category  # noqa: F401
from app.models.category_alias import CategoryAlias  # noqa: F401
from app.models.category_field import CategoryCoreField, CategoryOptionalField  # noqa: F401
from app.models.category_filter import CategoryFilter  # noqa: F401
from app.models.category_rule import CategoryRule  # noqa: F401
from app.models.chat import Chat  # noqa: F401
from app.models.vehicle import VehicleAlias, VehicleBrand, VehicleModel  # noqa: F401
from app.models.listing import Listing  # noqa: F401
from app.models.media import Media  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.message_attachment import MessageAttachment  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.saved_search import SavedSearch  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ("Base",)
