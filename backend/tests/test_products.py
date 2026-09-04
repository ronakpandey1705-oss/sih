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
