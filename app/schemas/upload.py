from pydantic import BaseModel
from typing import Optional

class FileUploadResponse(BaseModel):
    success: bool
    message: str
    file_url: Optional[str] = None
    file_path: Optional[str] = None
    bucket: Optional[str] = None

class FileDeleteResponse(BaseModel):
    success: bool
    message: str

class FileListResponse(BaseModel):
    files: list
    bucket: str
    folder: Optional[str] = None