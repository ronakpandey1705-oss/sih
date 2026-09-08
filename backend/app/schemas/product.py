from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    barcode: str = Field(..., description="EAN/UPC barcode number")
    name: str = Field(..., description="Packaged product name")
    brand: str = Field(..., description="Brand name")
    category: Optional[str] = Field(None, description="Product category")
    expected_net_quantity: str = Field(..., description="Expected net quantity (e.g. 200 g)")
    expected_mrp: str = Field(..., description="Expected MRP with currency symbol (e.g. ₹50)")
    manufacturer: str = Field(..., description="Manufacturer name")
    manufacturer_address: str = Field(..., description="Manufacturer location/address")
    packer: Optional[str] = Field(None, description="Packer name if distinct from manufacturer")
    importer: Optional[str] = Field(None, description="Importer name if imported")
    consumer_care_details: Optional[str] = Field(None, description="Consumer care contact details")
    is_demo: bool = Field(True, description="Flag indicating if this is fictional demo data")


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductLookupRequest(BaseModel):
    barcode: str = Field(..., examples=["8901234567890"], description="Barcode to look up")


class ProductLookupResponse(BaseModel):
    found: bool
    message: Optional[str] = None
    product: Optional[ProductResponse] = None


class BarcodeScanResponse(BaseModel):
    found: bool
    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    message: Optional[str] = None
    product: Optional[ProductResponse] = None

