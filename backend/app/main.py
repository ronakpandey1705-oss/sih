import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import (
    Product,
    Scan,
    UploadedImage,
    OCRResult,
    DetectedField,
    ComplianceResult,
    Violation,
    ComplaintReport
)
from app.services.products.product_service import ProductService
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
from app.api.chat import router as chat_router


def _ensure_sqlite_columns():
    """Ensure newly added columns exist in existing SQLite database tables."""
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(scans)"))
            existing_cols = {row[1] for row in result.fetchall()}
            migrations = [
                ("officer_id", "VARCHAR(64)"),
                ("establishment_name", "VARCHAR(255)"),
                ("inspection_location", "VARCHAR(255)"),
                ("officer_determination", "VARCHAR(64)"),
                ("officer_remarks", "TEXT"),
                ("officer_reviewed_at", "DATETIME"),
            ]
            for col_name, col_type in migrations:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE scans ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
        except Exception as e:
            print(f"[STARTUP] Notice during column check: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup and shutdown."""
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()

    # Seed demo fictional products if database is newly created
    db = SessionLocal()
    try:
        seeded = ProductService.seed_demo_products(db)
        if seeded > 0:
            print(f"[STARTUP] Seeded {seeded} fictional demo products into SQLite database.")
    finally:
        db.close()

    yield


FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "PackSure — SIH 2026 (Problem Statement SIH26034) AI-assisted packaged "
        "commodity Legal Metrology compliance screening."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS for frontend integration
origins = settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True if origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", summary="Service Health Check")
def health_check():
    """Health check endpoint required by system specification."""
    return {
        "status": "ok",
        "service": "packsure-backend"
    }


# Include API Routers
app.include_router(products_router, prefix="/api")
app.include_router(scans_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(inspections_router, prefix="/api")
app.include_router(inspections_images_router, prefix="/api")
app.include_router(compliance_router, prefix="/api")
app.include_router(inspections_compliance_router, prefix="/api")
app.include_router(public_compliance_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(inspections_reports_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_packsure():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {
        "message": "PackSure backend is running. Frontend files were not found.",
        "docs": "/docs",
        "health": "/api/health",
    }
