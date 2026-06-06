"""Shared SQLAlchemy ``Annotated`` column types."""

from __future__ import annotations

from typing import Annotated

from sqlalchemy import String
from sqlalchemy.orm import mapped_column

phone_str = Annotated[str, mapped_column(String(32), unique=True, index=True)]
