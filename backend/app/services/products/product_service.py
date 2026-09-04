from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate

# Fictional Demo Products for SIH 2026 Testing (All entries are fictional test fixtures)
DEMO_PRODUCTS = [
    {
        "barcode": "8901234567890",
        "name": "DemoBakes Choco Delight Biscuits",
        "brand": "DemoBakes (Fictional)",
        "category": "Biscuits & Confectionery",
        "expected_net_quantity": "200 g",
        "expected_mrp": "₹50",
        "manufacturer": "Demo Packaged Goods India Pvt Ltd",
        "manufacturer_address": "Plot 42, Fictional Industrial Area, Andheri East, Mumbai, Maharashtra 400093",
        "packer": "Demo Packaged Goods India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-000-DEMO, Email: care@demobakes.example.com",
        "is_demo": True
    },
    {
        "barcode": "8909876543210",
        "name": "PureHarvest Refined Sunflower Oil",
        "brand": "PureHarvest (Fictional)",
        "category": "Edible Oils",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹165",
        "manufacturer": "PureHarvest Agro Industries Ltd",
        "manufacturer_address": "Survey No. 108, Fictional Agro Corridor, Gandhinagar, Gujarat 382010",
        "packer": "PureHarvest Agro Industries Ltd",
        "importer": None,
        "consumer_care_details": "Customer Helpdesk: 079-00000000, Email: feedback@pureharvest.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901122334455",
        "name": "SparkleGlow Herbal Moisture Soap",
        "brand": "SparkleGlow (Fictional)",
        "category": "Personal Care",
        "expected_net_quantity": "125 g",
        "expected_mrp": "₹45",
        "manufacturer": "Sparkle Personal Care Laboratories",
        "manufacturer_address": "Khasra 25, Fictional Pharma Park, Baddi, Himachal Pradesh 173205",
        "packer": "Sparkle Personal Care Laboratories",
        "importer": None,
        "consumer_care_details": "Helpline: 1800-111-GLOW, Email: support@sparkleglow.example.com",
        "is_demo": True
    },
    {
        "barcode": "8905544332211",
        "name": "Spiceland Royal Garam Masala Powder",
        "brand": "Spiceland (Fictional)",
        "category": "Spices & Condiments",
        "expected_net_quantity": "100 g",
        "expected_mrp": "₹78",
        "manufacturer": "Spiceland Heritage Foods Co.",
        "manufacturer_address": "Sector 9, Fictional Spice Complex, Kochi, Kerala 682001",
        "packer": "Spiceland Heritage Foods Co.",
        "importer": None,
        "consumer_care_details": "Care Line: 0484-9999999, Email: spices@spiceland.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907788990011",
        "name": "GoldenGrain Sharbati Whole Wheat Atta",
        "brand": "GoldenGrain (Fictional)",
        "category": "Staples & Flours",
        "expected_net_quantity": "5 kg",
        "expected_mrp": "₹260",
        "manufacturer": "GoldenGrain Mills Private Limited",
        "manufacturer_address": "Grain Market Road, Fictional Agri Hub, Indore, Madhya Pradesh 452001",
        "packer": "GoldenGrain Mills Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-222-GRAIN, Email: feedback@goldengrain.example.com",
        "is_demo": True
    },
    {
        "barcode": "8906677889900",
        "name": "AromaPeak Premium Instant Coffee",
        "brand": "AromaPeak (Fictional)",
        "category": "Beverages",
        "expected_net_quantity": "50 g",
        "expected_mrp": "₹120",
        "manufacturer": "AromaPeak Plantation Beverages",
        "manufacturer_address": "Estate Rd 5, Fictional Hill Range, Chikmagalur, Karnataka 577101",
        "packer": "AromaPeak Plantation Beverages",
        "importer": None,
        "consumer_care_details": "Customer Service: 08262-888888, Email: coffee@aromapeak.example.com",
        "is_demo": True
    },
    {
        "barcode": "8904433221100",
        "name": "NutriBite California Roasted Almonds",
        "brand": "NutriBite (Fictional)",
        "category": "Dry Fruits & Nuts",
        "expected_net_quantity": "250 g",
        "expected_mrp": "₹340",
        "manufacturer": "NutriBite Foodworks LLP",
        "manufacturer_address": "Plot 15, Fictional Food Park, Sonipat, Haryana 131029",
        "packer": "NutriBite Foodworks LLP",
        "importer": "Global Dryfruit Traders, New Delhi 110006",
        "consumer_care_details": "Toll Free: 1800-333-NUTR, Email: wecare@nutribite.example.com",
        "is_demo": True
    },
    {
        "barcode": "8903322110099",
        "name": "FreshOrchard 100% Mixed Fruit Juice",
        "brand": "FreshOrchard (Fictional)",
        "category": "Beverages & Juices",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹130",
        "manufacturer": "FreshOrchard Beverage Bottlers",
        "manufacturer_address": "MIDC Phase 2, Fictional Industrial Zone, Pune, Maharashtra 411019",
        "packer": "FreshOrchard Beverage Bottlers",
        "importer": None,
        "consumer_care_details": "Customer Voice: 020-7777777, Email: service@freshorchard.example.com",
        "is_demo": True
    }
]


class ProductService:
    @staticmethod
    def seed_demo_products(db: Session) -> int:
        """Seed fictional demo products if none exist in the database."""
        count = db.query(Product).count()
        if count > 0:
            return 0

        seeded = 0
        for item in DEMO_PRODUCTS:
            product = Product(**item)
            db.add(product)
            seeded += 1
        db.commit()
        return seeded

    @staticmethod
    def get_by_barcode(db: Session, barcode: str) -> Optional[Product]:
        """Look up product by barcode string."""
        if not barcode:
            return None
        clean_barcode = barcode.strip()
        return db.query(Product).filter(Product.barcode == clean_barcode).first()

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def list_products(db: Session, skip: int = 0, limit: int = 50) -> List[Product]:
        return db.query(Product).offset(skip).limit(limit).all()

    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> Product:
        product = Product(**product_in.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
