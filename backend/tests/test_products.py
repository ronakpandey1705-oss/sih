def test_lookup_existing_demo_product(client):
    payload = {"barcode": "8901234567890"}
    response = client.post("/api/products/lookup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["product"] is not None
    assert data["product"]["barcode"] == "8901234567890"
    assert "Biscuits" in data["product"]["name"]
    assert data["product"]["expected_net_quantity"] == "200 g"
    assert data["product"]["expected_mrp"] == "₹50"
    assert data["product"]["is_demo"] is True


def test_lookup_unknown_barcode(client):
    payload = {"barcode": "9999999999999"}
    response = client.post("/api/products/lookup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert data["message"] == "Product not found in database"
    assert data["product"] is None


def test_list_products(client):
    response = client.get("/api/products/")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) >= 8
    barcodes = [p["barcode"] for p in products]
    assert "8901234567890" in barcodes
    assert "8909876543210" in barcodes


def test_get_product_by_id(client):
    # Lookup first to get an ID
    lookup_resp = client.post("/api/products/lookup", json={"barcode": "8901234567890"})
    prod_id = lookup_resp.json()["product"]["id"]

    response = client.get(f"/api/products/{prod_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prod_id
    assert data["barcode"] == "8901234567890"


def test_get_nonexistent_product_by_id(client):
    response = client.get("/api/products/99999")
    assert response.status_code == 404


def test_upsert_inspected_product(client):
    from tests.conftest import TestingSessionLocal
    from app.services.products.product_service import ProductService
    from app.models.scan import Scan
    from app.models.product import Product

    resp = client.post("/api/inspections/", json={"establishment_name": "New Mart", "inspection_location": "Delhi"})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        extracted = [
            {"field_name": "product_name", "value": "Aashirvaad Superior Atta"},
            {"field_name": "net_quantity", "value": "5 kg"},
            {"field_name": "mrp", "value": "₹ 310.00 (incl. of all taxes)"},
            {"field_name": "manufacturer_name_and_address", "value": "ITC Limited, 37 J.L. Nehru Road, Kolkata 700071"},
            {"field_name": "consumer_care", "value": "Toll Free: 1800-425-4444, Email: itccares@itc.in"}
        ]
        test_barcode = "8901030869999"
        prod = ProductService.upsert_inspected_product(
            db=db,
            scan_id=insp_id,
            barcode=test_barcode,
            extracted_fields=extracted
        )
        assert prod is not None
        assert prod.barcode == test_barcode
        assert prod.name == "Aashirvaad Superior Atta"
        assert prod.category == "Food & Beverages"
        assert prod.is_demo is False

        # Verify scan is linked
        scan = db.query(Scan).filter(Scan.id == insp_id).first()
        assert scan.product_id == prod.id

        # Verify it can be looked up via API
        lookup_resp = client.post("/api/products/lookup", json={"barcode": test_barcode})
        assert lookup_resp.status_code == 200
        assert lookup_resp.json()["found"] is True
        assert lookup_resp.json()["product"]["name"] == "Aashirvaad Superior Atta"
        assert lookup_resp.json()["product"]["is_demo"] is False
    finally:
        db.close()

