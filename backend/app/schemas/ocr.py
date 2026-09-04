from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


class OCRItemResponse(BaseModel):
    id: Optional[str] = Field(None, description="OCR item record ID")
    image_id: str = Field(..., description="Source image UUID")
    text: str = Field(..., description="Detected text content")
    confidence: float = Field(..., description="Recognition confidence (0.0 - 1.0)")
    bbox: List[int] = Field(..., description="Axis-aligned bounding box [x_min, y_min, x_max, y_max]")
    polygon: Optional[List[List[int]]] = Field(None, description="4-corner quad coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]")
    line_order: int = Field(0, description="Reading order index")

    model_config = ConfigDict(from_attributes=True)


class OCRScanResponse(BaseModel):
    scan_id: str = Field(..., description="Scan session ID")
    total_lines: int = Field(..., description="Total text lines detected")
    average_confidence: float = Field(..., description="Average OCR confidence score across all lines")
    items: List[OCRItemResponse] = Field(default_factory=list, description="All detected text blocks with coordinates")
