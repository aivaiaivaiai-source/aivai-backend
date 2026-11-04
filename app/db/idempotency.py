"""Helpers for concurrent idempotent inserts under unique constraints."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_unique_violation(exc: BaseException, *constraint_names: str) -> bool:
    """True when ``exc`` (or its cause chain) is a unique violation of named constraints."""
    wanted = {name.lower() for name in constraint_names if name}
    if not wanted:
        return False

    stack: list[BaseException | None] = [exc]
    seen: set[int] = set()
    while stack:
        cur = stack.pop()
        if cur is None or id(cur) in seen:
            continue
        seen.add(id(cur))

        cname = getattr(cur, "constraint_name", None)
        if isinstance(cname, str) and cname.lower() in wanted:
            return True

        diag = getattr(cur, "diag", None)
        if diag is not None:
            dname = getattr(diag, "constraint_name", None)
            if isinstance(dname, str) and dname.lower() in wanted:
                return True

        blob = str(cur).lower()
        if any(name in blob for name in wanted):
            return True

        stack.append(getattr(cur, "orig", None))
        stack.append(cur.__cause__)
        stack.append(cur.__context__)
    return False


async def insert_or_get_on_unique(
    session: AsyncSession,
    *,
    insert: Callable[[], Awaitable[T]],
    fetch_existing: Callable[[], Awaitable[T | None]],
    constraint_names: tuple[str, ...],
    reused_log: str,
    reused_log_args: tuple[object, ...] = (),
) -> T:
    """
    Insert under a SAVEPOINT; on expected unique conflict, re-fetch and return existing.

    Keeps the outer transaction usable so concurrent media-complete work is not rolled back.
    """
    try:
        async with session.begin_nested():
            return await insert()
    except IntegrityError as exc:
        if not is_unique_violation(exc, *constraint_names):
            raise
        existing = await fetch_existing()
        if existing is None:
            raise
        logger.info(reused_log, *reused_log_args)
        return existing
