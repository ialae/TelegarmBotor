"""Pydantic model for the shared ``ideas`` collection."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class IdeaCategory(str, Enum):
    """Allowed categories for ideas."""

    LEARNING = "Learning"
    SAAS = "SaaS"
    AI = "AI"
    LOCAL_BUSINESS = "Local Business"
    HEALTH = "Health"
    WORK = "Work"
    MOVIES = "Movies"
    SERIES = "Series"
    LIFE = "Life"
    FAMILY = "Family"
    TRAVEL = "Travel"


# Maps user-friendly shortcuts (lowercase) → enum member.
CATEGORY_ALIASES: dict[str, IdeaCategory] = {
    "learning": IdeaCategory.LEARNING,
    "saas": IdeaCategory.SAAS,
    "ai": IdeaCategory.AI,
    "local business": IdeaCategory.LOCAL_BUSINESS,
    "local": IdeaCategory.LOCAL_BUSINESS,
    "business": IdeaCategory.LOCAL_BUSINESS,
    "health": IdeaCategory.HEALTH,
    "work": IdeaCategory.WORK,
    "movies": IdeaCategory.MOVIES,
    "movie": IdeaCategory.MOVIES,
    "series": IdeaCategory.SERIES,
    "life": IdeaCategory.LIFE,
    "family": IdeaCategory.FAMILY,
    "travel": IdeaCategory.TRAVEL,
}


def resolve_category(text: str) -> IdeaCategory | None:
    """Match free-form text to an ``IdeaCategory``, or ``None`` if invalid.

    Matching is case-insensitive and supports aliases like ``"local"``
    for ``Local Business``.
    """
    return CATEGORY_ALIASES.get(text.strip().lower())


def format_category_options() -> str:
    """Return a numbered list of categories for display in Telegram."""
    lines: list[str] = []
    for idx, member in enumerate(IdeaCategory, start=1):
        lines.append(f"  {idx}. {member.value}")
    return "\n".join(lines)


def resolve_category_by_number(number: int) -> IdeaCategory | None:
    """Return the category at the given 1-based position, or ``None``."""
    members = list(IdeaCategory)
    if 1 <= number <= len(members):
        return members[number - 1]
    return None


class Idea(BaseModel):
    """A single idea or thought."""

    title: str
    description: str = ""
    category: IdeaCategory
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
