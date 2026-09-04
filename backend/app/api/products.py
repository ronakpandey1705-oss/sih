from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import (
    ProductLookupRequest,
    ProductLookupResponse,
    ProductResponse,
    ProductCreate
)
from app.services.products.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/lookup", response_model=ProductLookupResponse, summary="Look up packaged product by barcode")
def lookup_product(
    payload: ProductLookupRequest,
    db: Session = Depends(get_db)
):
    """
    Look up a product in the verified reference database by barcode.
    If not found, returns found=false without failing the scan workflow,
    allowing image/label analysis to proceed normally.
    """
    barcode = payload.barcode.strip()
    product = ProductService.get_by_barcode(db, barcode)

    if not product:
        return ProductLookupResponse(
            found=False,
            message="Product not found in database",
            product=None
        )

    return ProductLookupResponse(
        found=True,
        message="Product found in reference database",
        product=ProductResponse.model_validate(product)
    )


@router.get("/", response_model=List[ProductResponse], summary="List registered reference/demo products")
def list_products(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List reference/demo products currently available in the database."""
    products = ProductService.list_products(db, skip=skip, limit=limit)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product details by ID")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get single product details by internal database ID."""
    product = ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return ProductResponse.model_validate(product)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="Add a new product")
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db)
):
    """Add a new product to the reference database."""
    existing = ProductService.get_by_barcode(db, product_in.barcode)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with barcode '{product_in.barcode}' already exists"
        )
    product = ProductService.create_product(db, product_in)
    return ProductResponse.model_validate(product)
