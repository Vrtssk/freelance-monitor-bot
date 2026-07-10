from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    """Normalized job posting from any freelance exchange."""

    source: str
    external_id: str
    title: str
    description: str = ""
    budget: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    matched_topics: list[str] = Field(default_factory=list)
    match_reason: Optional[str] = None

    @property
    def unique_key(self) -> str:
        return f"{self.source}:{self.external_id}"

    @property
    def text_for_filter(self) -> str:
        parts = [self.title, self.description or "", self.category or ""]
        return " ".join(parts).lower()
