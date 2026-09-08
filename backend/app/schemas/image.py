from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ImageUploadResponse(BaseModel):
    image_id: str = Field(..., description="Unique UUID of the uploaded image")
    scan_id: str = Field(..., description="Scan session ID")
    filename: str = Field(..., description="Original filename")
    file_size: Optional[int] = Field(None, description="Size in bytes")
    mime_type: Optional[str] = Field(None, description="Image MIME type")
    created_at: datetime
    preprocessed: bool = Field(False, description="Whether preprocessing has been executed")
    barcode_detected: bool = Field(False, description="Whether a barcode was automatically detected from the image")
    detected_barcode: Optional[str] = Field(None, description="Automatically decoded barcode string if present")

    model_config = ConfigDict(from_attributes=True)


class ImageDetailResponse(BaseModel):
    id: str
    scan_id: str
    filename: str
    original_path: str
    preprocessed_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreprocessResultResponse(BaseModel):
    image_id: str
    scan_id: str
    preprocessed_path: str
    original_dimensions: List[int] = Field(..., description="[height, width]")
    preprocessed_dimensions: List[int] = Field(..., description="[height, width]")
    skew_angle_detected: float = Field(0.0, description="Detected rotation skew angle in degrees")
    clahe_applied: bool = True
    denoised: bool = True
