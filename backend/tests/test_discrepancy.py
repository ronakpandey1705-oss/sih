import pytest
from app.models.scan import Scan
from app.models.detected_field import DetectedField
from app.services.discrepancy.discrepancy_service import DiscrepancyService
from tests.conftest import TestingSessionLocal


def test_discrepancy_matching_catalog_product(client):
    # DemoBakes Choco Delight Biscuits has barcode 8901234567890, Net Qty: 200 g, MRP: 50.0
    resp = client.post("/api/inspections/", json={"barcode": "8901234567890"})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        # Add matching package declarations
        df1 = DetectedField(scan_id=insp_id, field_name="net_quantity", value="200 g", confidence=0.95)
        df2 = DetectedField(scan_id=insp_id, field_name="mrp", value="₹ 50.00 (incl. of all taxes)", confidence=0.95)
        df3 = DetectedField(scan_id=insp_id, field_name="product_name", value="DemoBakes Choco Delight Biscuits", confidence=0.95)
        for d in [df1, df2, df3]:
            db.add(d)
        db.commit()

        disc_data = DiscrepancyService.check_discrepancies(insp_id, db)
        assert disc_data["has_catalog_baseline"] is True
        assert disc_data["total_discrepancies"] == 0
        assert "match" in disc_data["summary"].lower()
    finally:
        db.close()


def test_discrepancy_overcharging_and_quantity_mismatch(client):
    # Catalog: Net Qty 200 g, MRP 50.0
    resp = client.post("/api/inspections/", json={"barcode": "8901234567890"})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        # Package declares 180 g (mismatch) and MRP ₹65 (overcharging)
        df1 = DetectedField(scan_id=insp_id, field_name="net_quantity", value="180 g", confidence=0.95)
        df2 = DetectedField(scan_id=insp_id, field_name="mrp", value="₹ 65.00", confidence=0.95)
        db.add(df1)
        db.add(df2)
        db.commit()

        disc_data = DiscrepancyService.check_discrepancies(insp_id, db)
        assert disc_data["total_discrepancies"] >= 2
        status_map = {d["field"]: d["status"] for d in disc_data["discrepancies"]}
        assert status_map.get("net_quantity") == "POTENTIAL_DISCREPANCY"
        assert status_map.get("mrp") == "POTENTIAL_DISCREPANCY"
    finally:
        db.close()


def test_discrepancy_conservative_unregistered_barcode(client):
    # Barcode not in catalog -> should return NEEDS_REVIEW rather than non-compliance
    resp = client.post("/api/inspections/", json={"barcode": "9999999999999"})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        disc_data = DiscrepancyService.check_discrepancies(insp_id, db)
        assert disc_data["has_catalog_baseline"] is False
        assert disc_data["total_discrepancies"] == 0
        assert disc_data["items_needing_review"] == 1
        assert disc_data["discrepancies"][0]["status"] == "NEEDS_REVIEW"
    finally:
        db.close()


def test_discrepancy_conservative_unscanned_barcode(client):
    # No barcode provided -> conservative check returns NEEDS_REVIEW
    resp = client.post("/api/inspections/", json={})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        disc_data = DiscrepancyService.check_discrepancies(insp_id, db)
        assert disc_data["has_catalog_baseline"] is False
        assert disc_data["total_discrepancies"] == 0
        assert disc_data["items_needing_review"] == 1
    finally:
        db.close()
