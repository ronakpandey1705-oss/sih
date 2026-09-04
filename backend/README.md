# SIH 2026: Legal Metrology (Packaged Commodities) AI Screening Backend
**Problem Statement ID:** SIH26034  
**Project:** AI-assisted web application for Legal Metrology Packaged Commodities compliance screening, violation detection, evidence logging, and complaint generation.

---

## Architecture Overview (Phase 1)
- **Framework:** FastAPI (Python 3.10+)
- **Database:** SQLite with SQLAlchemy ORM (2.0+)
- **Validation:** Pydantic v2
- **Documentation:** Interactive OpenAPI / Swagger UI enabled at `/docs` and `/redoc`
- **CORS:** Configurable via `.env` (defaults to `*` for frontend development)

---

## Quickstart Guide

### 1. Environment Setup
```powershell
# Navigate to backend directory
cd C:\Users\Himanshu Varma\.gemini\antigravity\scratch\backend

# Activate virtual environment
..\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` if not already present:
```powershell
cp .env.example .env
```

### 3. Run the Backend Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive API Docs (Swagger): `http://localhost:8000/docs`
- Alternative Docs (ReDoc): `http://localhost:8000/redoc`

### 4. Run Automated Tests
```powershell
pytest -v
```

---

## API Endpoints (Phase 1 Frontend Contract)

### 1. Health Check
- **URL:** `GET /api/health`
- **Description:** Verify backend service status.
- **Headers:** `Content-Type: application/json`
- **Response `200 OK`:**
```json
{
  "status": "ok",
  "service": "legal-metrology-backend"
}
```

---

### 2. Product Barcode Lookup
- **URL:** `POST /api/products/lookup`
- **Description:** Looks up packaged product by scanned barcode. If not found in the reference database, returns `found: false` without failing the session, allowing user to proceed to label image scan.
- **Request Body:**
```json
{
  "barcode": "8901234567890"
}
```
- **Response `200 OK` (Product Found):**
```json
{
  "found": true,
  "message": "Product found in reference database",
  "product": {
    "id": 1,
    "barcode": "8901234567890",
    "name": "DemoBakes Choco Delight Biscuits",
    "brand": "DemoBakes (Fictional)",
    "category": "Biscuits & Confectionery",
    "expected_net_quantity": "200 g",
    "expected_mrp": "₹50",
    "manufacturer": "Demo Packaged Goods India Pvt Ltd",
    "manufacturer_address": "Plot 42, Fictional Industrial Area, Andheri East, Mumbai, Maharashtra 400093",
    "packer": "Demo Packaged Goods India Pvt Ltd",
    "importer": null,
    "consumer_care_details": "Toll Free: 1800-000-DEMO, Email: care@demobakes.example.com",
    "is_demo": true,
    "created_at": "2026-09-03T08:00:00Z"
  }
}
```
- **Response `200 OK` (Unknown Barcode):**
```json
{
  "found": false,
  "message": "Product not found in database",
  "product": null
}
```

---

### 3. Create Scan Session
- **URL:** `POST /api/scans`
- **Description:** Starts a new scan session. Associates known product if barcode matches; handles unlisted/omitted barcode seamlessly.
- **Request Body:**
```json
{
  "barcode": "8901234567890",
  "user_location": "Bandra, Mumbai",
  "notes": "Optional inspection note"
}
```
- **Response `201 Created`:**
```json
{
  "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "barcode": "8901234567890",
  "status": "CREATED",
  "created_at": "2026-09-03T08:00:00Z"
}
```

---

### 4. Get Scan Session Details
- **URL:** `GET /api/scans/{scan_id}`
- **Description:** Retrieve the scan status, linked product data, score, and image count.
- **Response `200 OK`:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "barcode": "8901234567890",
  "product_id": 1,
  "product": {
    "id": 1,
    "barcode": "8901234567890",
    "name": "DemoBakes Choco Delight Biscuits",
    "brand": "DemoBakes (Fictional)",
    "expected_net_quantity": "200 g",
    "expected_mrp": "₹50",
    "manufacturer": "Demo Packaged Goods India Pvt Ltd",
    "manufacturer_address": "Plot 42, Fictional Industrial Area, Andheri East, Mumbai, Maharashtra 400093",
    "packer": "Demo Packaged Goods India Pvt Ltd",
    "importer": null,
    "consumer_care_details": "Toll Free: 1800-000-DEMO, Email: care@demobakes.example.com",
    "is_demo": true,
    "created_at": "2026-09-03T08:00:00Z"
  },
  "status": "CREATED",
  "overall_score": null,
  "risk_level": null,
  "user_location": "Bandra, Mumbai",
  "notes": "Optional inspection note",
  "created_at": "2026-09-03T08:00:00Z",
  "images_count": 0
}
```

---

### 5. List Reference Products
- **URL:** `GET /api/products/`
- **Description:** Returns all reference/demo products in the database.
- **Query Params:** `skip=0`, `limit=50`

---

## Phase 2 Endpoints: Image Upload, Vision Preprocessing & PaddleOCR

### 6. Upload Packaging Image
- **URL:** `POST /api/scans/{scan_id}/images`
- **Description:** Uploads a package photograph (JPG, PNG, WebP). Saves original image safely as legal evidence.
- **Headers:** `Content-Type: multipart/form-data`
- **Form Data:**
  - `file`: binary file (required)
  - `user_location`: string (optional, e.g. `"Bandra, Mumbai"`)
- **Response `201 Created`:**
```json
{
  "image_id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
  "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "label.jpg",
  "file_size": 245120,
  "mime_type": "image/jpeg",
  "created_at": "2026-09-03T08:30:00Z",
  "preprocessed": false
}
```

---

### 7. List Uploaded Images for Scan
- **URL:** `GET /api/scans/{scan_id}/images`
- **Description:** Returns all packaging photos associated with the session.
- **Response `200 OK`:**
```json
[
  {
    "id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
    "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "filename": "label.jpg",
    "original_path": "./uploads/3fa85f64.../90e66c2d....jpg",
    "preprocessed_path": null,
    "file_size": 245120,
    "mime_type": "image/jpeg",
    "created_at": "2026-09-03T08:30:00Z"
  }
]
```

---

### 8. OpenCV Image Preprocessing
- **URL:** `POST /api/scans/{scan_id}/images/{image_id}/preprocess`
- **Description:** Runs the OpenCV image enhancement pipeline (CLAHE contrast equalization, bilateral denoising, aspect-ratio resizing, and text deskewing). Original image is untouched.
- **Query Params:** `deskew=true` (optional, default: true)
- **Response `200 OK`:**
```json
{
  "image_id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
  "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "preprocessed_path": "./uploads/3fa85f64.../90e66c2d..._preprocessed.png",
  "original_dimensions": [1080, 1920],
  "preprocessed_dimensions": [1080, 1920],
  "skew_angle_detected": -1.24,
  "clahe_applied": true,
  "denoised": true
}
```

---

### 9. Run PaddleOCR on Image
- **URL:** `POST /api/scans/{scan_id}/images/{image_id}/ocr`
- **Description:** Executes PaddleOCR detection & recognition. Automatically uses the preprocessed image if available (or creates one). Returns detected text lines, confidence scores, bounding boxes (`[x_min, y_min, x_max, y_max]`), and 4-corner polygon coordinates.
- **Query Params:** `use_preprocessed=true` (optional, default: true)
- **Response `200 OK`:**
```json
[
  {
    "id": "f5127021-ba32-47d0-a0eb-d1cf57ae8c14",
    "image_id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
    "text": "MRP Rs. 50.00",
    "confidence": 0.9987,
    "bbox": [50, 68, 280, 96],
    "polygon": [[50, 68], [280, 68], [280, 96], [50, 96]],
    "line_order": 0
  },
  {
    "id": "e4029411-cf51-4190-b1fb-a8bc43de7112",
    "image_id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
    "text": "Net Qty: 200 g",
    "confidence": 0.9992,
    "bbox": [50, 148, 275, 175],
    "polygon": [[50, 148], [275, 148], [275, 175], [50, 175]],
    "line_order": 1
  }
]
```

---

### 10. Get All OCR Results for Scan (Frontend Box Overlay Contract)
- **URL:** `GET /api/scans/{scan_id}/ocr`
- **Description:** Retrieves all detected OCR lines and bounding boxes for the scan session. Used by the frontend to render interactive highlight boxes over packaging photos.
- **Response `200 OK`:**
```json
{
  "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total_lines": 2,
  "average_confidence": 0.9989,
  "items": [
    {
      "id": "f5127021-ba32-47d0-a0eb-d1cf57ae8c14",
      "image_id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
      "text": "MRP Rs. 50.00",
      "confidence": 0.9987,
      "bbox": [50, 68, 280, 96],
      "polygon": [[50, 68], [280, 68], [280, 96], [50, 96]],
      "line_order": 0
    },
    {
      "id": "e4029411-cf51-4190-b1fb-a8bc43de7112",
      "image_id": "90e66c2d-cf48-4395-9276-eb34d3d827f8",
      "text": "Net Qty: 200 g",
      "confidence": 0.9992,
      "bbox": [50, 148, 275, 175],
      "polygon": [[50, 148], [275, 148], [275, 175], [50, 175]],
      "line_order": 1
    }
  ]
}
```

---

## Phase 3: Legal Metrology Ruleset, Field Extraction & Compliance Screening

### Active Endpoints for Phase 3

#### 1. Get Ruleset Configuration
`GET /api/compliance/rules`
Returns the active Legal Metrology ruleset loaded directly from `rules/rules.json`, including:
- Rules `LM-01` through `LM-10`
- Rule 7 minimum numeral font size matrix
- Schedule I Maximum Permissible Errors (MPE) tolerance limits
- Schedule II status (2022 amendment: standard pack sizes relaxed; mandatory Unit Sale Price)
- Rule 26 package size exemptions (<= 10 g / ml)
- Statutory amendments

#### 2. Extract Fields from OCR
`POST /api/inspections/{inspection_id}/extract-fields` (and `/api/scans/{scan_id}/extract-fields`)
Runs NLP and regex heuristics over OCR lines and bounding boxes to extract:
- `product_name`
- `net_quantity`
- `mrp`
- `unit_sale_price`
- `manufacturer_name_and_address`
- `consumer_care`
- `manufacture_or_import_date`
- `dimensions`
Supports English and Hindi (Devanagari script) declarations.

#### 3. Run Compliance Evaluation
`POST /api/inspections/{inspection_id}/evaluate` (and `/api/scans/{scan_id}/evaluate`)
Evaluates extracted fields against all rules in `rules.json`.
- Statuses returned for each rule: `PASS`, `POTENTIAL_NON_COMPLIANCE`, `NEEDS_REVIEW`, `NOT_APPLICABLE`
- Calculates overall AI compliance screening score (0 to 100%) and risk level (`LOW`, `MEDIUM`, `HIGH`)
- Populates `compliance_results` and `violations` database tables

#### 4. Get Compliance Results
`GET /api/inspections/{inspection_id}/compliance` (and `/api/scans/{scan_id}/compliance`)
Retrieves the full compliance evaluation results and officer summary.

#### 5. Record Officer Review & Determination
`POST /api/inspections/{inspection_id}/review`
Allows the inspecting government officer to record their official determination (`COMPLIANT`, `POTENTIAL_NON_COMPLIANCE_CONFIRMED`, `FURTHER_INVESTIGATION`, `DISMISSED`) and official written remarks.

---

## Phase 4: Inspection Report, Evidence Package & Discrepancy Detection

### Active Endpoints for Phase 4

#### 1. Collated Evidence Package
- **URL:** `GET /api/inspections/{inspection_id}/evidence` (alias `/api/scans/{scan_id}/evidence`)
- **Description:** Aggregates packaging photos, OCR bounding box polygons, detected declaration coordinates, compliance evaluations, and discrepancy findings into a cohesive payload for frontend canvas highlight rendering.

#### 2. Catalog vs Packaging Discrepancies
- **URL:** `GET /api/inspections/{inspection_id}/discrepancies` (alias `/api/scans/{scan_id}/discrepancies`)
- **Description:** Performs conservative comparison of registered catalog product baseline against observed package declarations:
  - **Net Quantity:** Detects quantity variance (e.g., catalog 200g vs package 180g).
  - **MRP / Overcharging:** Detects if printed package price exceeds catalog baseline.
  - **Conservative Guardrail:** If catalog baseline is missing/unregistered or evidence is insufficient, returns `NEEDS_REVIEW` rather than assuming non-compliance. Never asserts guilt automatically.

#### 3. Unified One-Shot Screening Endpoint
- **URL:** `POST /api/inspections/{inspection_id}/analyze` (alias `/api/scans/{scan_id}/analyze`)
- **Description:** Single endpoint for frontend convenience that:
  1. Triggers PaddleOCR if images exist without OCR.
  2. Extracts declarations via `FieldExtractor`.
  3. Evaluates compliance against `rules/rules.json`.
  4. Detects catalog discrepancies via `DiscrepancyService`.
  5. Returns comprehensive screening scores, risk level, and rule summaries in one response.

#### 4. Official Inspection Notice & Report Generation (PDF + JSON)
- **URL:** `POST /api/inspections/{inspection_id}/report` (alias `/api/scans/{scan_id}/report`)
- **Description:** Generates the official Legal Metrology Inspection Notice and Report:
  - Generates publication-ready PDF using ReportLab with government layout, statutory disclaimers under the Legal Metrology Act, 2009, compliance matrix, discrepancy table, and official signature blocks.
  - Persists report record in `complaint_reports` table.
- **Request Body (Optional):**
```json
{
  "officer_notes": "Surveillance inspection at commercial premises",
  "authority_name": "Legal Metrology Organization, Govt. of Maharashtra",
  "authority_jurisdiction": "Mumbai Suburban Division"
}
```

#### 5. Retrieve Inspection Report
- **URL:** `GET /api/inspections/{inspection_id}/report` (alias `/api/scans/{scan_id}/report`)
- **Description:** Retrieves the existing report metadata, summary, and full JSON payload.

#### 6. Download Official Report PDF
- **URL:** `GET /api/inspections/{inspection_id}/report/pdf` (alias `/api/scans/{scan_id}/report/pdf`)
- **Description:** Streams the downloadable PDF file (`application/pdf`) for printing, archiving, or official notice delivery.

---

## Pre-loaded Fictional Demo Barcodes
For testing before frontend camera barcode scanner is wired:

| Barcode | Product Name | Category | Expected Net Qty | Expected MRP |
|---|---|---|---|---|
| `8901234567890` | DemoBakes Choco Delight Biscuits | Biscuits & Confectionery | 200 g | ₹50 |
| `8909876543210` | PureHarvest Refined Sunflower Oil | Edible Oils | 1 L | ₹165 |
| `8901122334455` | SparkleGlow Herbal Moisture Soap | Personal Care | 125 g | ₹45 |
| `8905544332211` | Spiceland Royal Garam Masala Powder | Spices & Condiments | 100 g | ₹78 |
| `8907788990011` | GoldenGrain Sharbati Whole Wheat Atta | Staples & Flours | 5 kg | ₹260 |
| `8906677889900` | AromaPeak Premium Instant Coffee | Beverages | 50 g | ₹120 |
| `8904433221100` | NutriBite California Roasted Almonds | Dry Fruits & Nuts | 250 g | ₹340 |
| `8903322110099` | FreshOrchard 100% Mixed Fruit Juice | Beverages & Juices | 1 L | ₹130 |

*Note: All demo products are fictional and marked `is_demo = True` for SIH 2026 testing.*
