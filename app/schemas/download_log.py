from typing import Optional

from pydantic import BaseModel


class DownloadLogFilter(BaseModel):
    page: int
    page_size: int
    downloader: Optional[str] = None
    save_path: Optional[str] = None
