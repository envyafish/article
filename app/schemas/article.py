from typing import Optional

from pydantic import BaseModel, Field


class ArticleQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: Optional[str] = None
    section: Optional[str] = None
    category: Optional[str] = None
