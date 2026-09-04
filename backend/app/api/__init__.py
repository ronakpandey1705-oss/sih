from app.api.products import router as products_router
from app.api.scans import router as scans_router, inspections_router
from app.api.images import router as images_router, inspections_images_router
from app.api.compliance import (
    router as compliance_router,
    inspections_compliance_router,
    public_compliance_router
)
from app.api.reports import (
    router as reports_router,
    inspections_reports_router
)

__all__ = [
    "products_router",
    "scans_router",
    "inspections_router",
    "images_router",
    "inspections_images_router",
    "compliance_router",
    "inspections_compliance_router",
    "public_compliance_router",
    "reports_router",
    "inspections_reports_router"
]
