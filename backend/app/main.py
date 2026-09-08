import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
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
from app.api.officers import router as officers_router


def _ensure_sqlite_columns():
    """Ensure newly added columns exist in existing SQLite database tables."""
    if not str(engine.url).startswith("sqlite"):
        return
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


def _seed_demo_officers(db) -> int:
    """Seed authorized Legal Metrology Enforcement Officers into database."""
    from app.models.officer import Officer
    DEMO_OFFICERS = [
        {
            "officer_badge": "LM-2026-001",
            "name": "Ronak Pandey",
            "email": "ronak.pandey@gmail.com",
            "provider": "gmail",
            "designation": "Senior Legal Metrology Enforcement Officer",
            "jurisdiction": "National Directorate, New Delhi",
            "status": "ACTIVE"
        },
        {
            "officer_badge": "LM-2026-001-GOV",
            "name": "Ronak Pandey",
            "email": "ronak.pandey@gov.in",
            "provider": "gov",
            "designation": "Senior Legal Metrology Enforcement Officer",
            "jurisdiction": "National Directorate, New Delhi",
            "status": "ACTIVE"
        },
        {
            "officer_badge": "LM-2026-002",
            "name": "Himanshu Verma",
            "email": "himanshu.verma@gmail.com",
            "provider": "gmail",
            "designation": "Inspector Legal Metrology (Packaging Verification)",
            "jurisdiction": "Western Zone, Mumbai",
            "status": "ACTIVE"
        },
        {
            "officer_badge": "LM-2026-003",
            "name": "Vibha Pawar",
            "email": "vibha.pawar@yahoo.com",
            "provider": "yahoo",
            "designation": "Assistant Controller Legal Metrology",
            "jurisdiction": "Northern Zone, Chandigarh",
            "status": "ACTIVE"
        },
        {
            "officer_badge": "LM-2026-004",
            "name": "Harsh Nagvekar",
            "email": "harsh.nagvekar@icloud.com",
            "provider": "apple",
            "designation": "State Metrology Verification Specialist",
            "jurisdiction": "Southern Zone, Bengaluru",
            "status": "ACTIVE"
        },
    ]
    updated = 0
    for item in DEMO_OFFICERS:
        existing = db.query(Officer).filter(Officer.email == item["email"]).first()
        if not existing:
            db.add(Officer(**item))
            updated += 1
        else:
            for k, v in item.items():
                setattr(existing, k, v)
            updated += 1
    # Clean out any legacy mock officers
    allowed_emails = {item["email"] for item in DEMO_OFFICERS}
    legacy = db.query(Officer).filter(~Officer.email.in_(allowed_emails)).all()
    for leg in legacy:
        db.delete(leg)
    db.commit()
    return updated


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup and shutdown."""
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()

    # Seed demo fictional products and authorized officers
    db = SessionLocal()
    try:
        seeded = ProductService.seed_demo_products(db)
        if seeded > 0:
            print(f"[STARTUP] Seeded {seeded} fictional demo products into SQLite database.")
        seeded_officers = _seed_demo_officers(db)
        if seeded_officers > 0:
            print(f"[STARTUP] Seeded {seeded_officers} authorized legal metrology officers.")
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
app.include_router(officers_router, prefix="/api")


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


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=404,
                content={"detail": exc.detail or "API endpoint not found"}
            )
        four_o_four_path = os.path.join(FRONTEND_DIR, "404.html")
        if os.path.isfile(four_o_four_path):
            return FileResponse(four_o_four_path, status_code=404)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

