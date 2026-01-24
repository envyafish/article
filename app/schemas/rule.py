from typing import Optional

from pydantic import BaseModel


class RuleForm(BaseModel):
    id: Optional[int] = None
    section: str
    category: str
    regex: Optional[str] = None
    downloader: str
    save_path: str
