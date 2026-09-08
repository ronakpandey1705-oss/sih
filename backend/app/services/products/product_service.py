from typing import Optional, List, Any, Dict
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate

# Comprehensive Reference Product Catalog for Legal Metrology (Packaged Commodities) Rules, 2011 Verification
DEMO_PRODUCTS = [
    # --- 1. BEDDING, TEXTILES & HOME FURNISHINGS ---
    {
        "barcode": "8908877665501",
        "name": "Signature 100% Pure Cotton Double Bedsheet Set",
        "brand": "Heritage Home Textiles",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Bedsheet: 228 cm x 274 cm, 2 Pillow Covers: 46 cm x 69 cm)",
        "expected_mrp": "₹1,299",
        "manufacturer": "Heritage Weaves & Looms Pvt Ltd",
        "manufacturer_address": "Plot 18, Textile Industrial Park, Surat, Gujarat 395002",
        "packer": "Heritage Weaves & Looms Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-444-HOME, Email: support@heritagetextiles.example.com",
        "is_demo": True
    },
    {
        "barcode": "8908877665502",
        "name": "Royal Comfort King Size All-Around Elastic Fitted Bedsheet",
        "brand": "Urban Bedding Co.",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Fitted Sheet: 198 cm x 198 cm x 25 cm, 2 Pillow Covers: 46 cm x 69 cm)",
        "expected_mrp": "₹1,499",
        "manufacturer": "Urban Living Furnishings India LLP",
        "manufacturer_address": "Sector 29, Industrial Area, Panipat, Haryana 132103",
        "packer": "Urban Living Furnishings India LLP",
        "importer": None,
        "consumer_care_details": "Customer Helpdesk: 0180-2223333, Email: care@urbanbedding.example.com",
        "is_demo": True
    },
    {
        "barcode": "8908877665503",
        "name": "Daily Comfort Single Cotton Bedsheet with Pillow Cover",
        "brand": "LoomCraft",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Bedsheet: 152 cm x 228 cm, 1 Pillow Cover: 46 cm x 69 cm)",
        "expected_mrp": "₹599",
        "manufacturer": "LoomCraft Mills Private Limited",
        "manufacturer_address": "Avinashi Road, Tirupur, Tamil Nadu 641604",
        "packer": "LoomCraft Mills Private Limited",
        "importer": None,
        "consumer_care_details": "Helpline: 0421-4455667, Email: service@loomcraft.example.com",
        "is_demo": True
    },
    {
        "barcode": "8908877665504",
        "name": "Plush Velvet 500 GSM Pure Cotton Bath Towel",
        "brand": "HydroSoft",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Dimensions: 70 cm x 140 cm)",
        "expected_mrp": "₹499",
        "manufacturer": "HydroSoft Terryfab Mills Ltd",
        "manufacturer_address": "MIDC Industrial Estate, Solapur, Maharashtra 413006",
        "packer": "HydroSoft Terryfab Mills Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-555-SOFT, Email: care@hydrosoft.example.com",
        "is_demo": True
    },
    {
        "barcode": "8908877665505",
        "name": "Thermal Insulated Blackout Door Curtains (Set of 2)",
        "brand": "DrapeStyle",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "2 N (Dimensions each: 116 cm x 213 cm / 7 Feet)",
        "expected_mrp": "₹1,199",
        "manufacturer": "DrapeStyle Decor India Ltd",
        "manufacturer_address": "Textile Corridor, Bhilwara, Rajasthan 311001",
        "packer": "DrapeStyle Decor India Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 01482-234567, Email: support@drapestyle.example.com",
        "is_demo": True
    },
    {
        "barcode": "8908877665506",
        "name": "Embossed Jacquard Velvet Cushion Covers (Set of 5)",
        "brand": "Heritage Home Textiles",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "5 N (Dimensions each: 40 cm x 40 cm / 16 x 16 Inch)",
        "expected_mrp": "₹649",
        "manufacturer": "Heritage Weaves & Looms Pvt Ltd",
        "manufacturer_address": "Plot 18, Textile Industrial Park, Surat, Gujarat 395002",
        "packer": "Heritage Weaves & Looms Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-444-HOME, Email: support@heritagetextiles.example.com",
        "is_demo": True
    },
    {
        "barcode": "8908877665507",
        "name": "All-Season Pure Cotton Microfiber AC Dohar Quilt",
        "brand": "Urban Bedding Co.",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Dimensions: 220 cm x 240 cm)",
        "expected_mrp": "₹1,899",
        "manufacturer": "Urban Living Furnishings India LLP",
        "manufacturer_address": "Sector 29, Industrial Area, Panipat, Haryana 132103",
        "packer": "Urban Living Furnishings India LLP",
        "importer": None,
        "consumer_care_details": "Customer Helpdesk: 0180-2223333, Email: care@urbanbedding.example.com",
        "is_demo": True
    },

    # --- 2. ELECTRONICS, APPLIANCES & GADGETS ---
    {
        "barcode": "8906038530187",
        "name": "Envie ECR-20 Rechargeable Battery Charger (Beetle)",
        "brand": "Envie",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Includes Charger for 2/4 AA/AAA Ni-MH/Ni-CD Batteries)",
        "expected_mrp": "₹345",
        "manufacturer": "Envie Electronic Systems India Pvt Ltd",
        "manufacturer_address": "D-108, Okhla Industrial Area Phase 1, New Delhi 110020",
        "packer": "Envie Electronic Systems India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Customer Care: 011-45678900, Email: care@envie.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554401",
        "name": "Apex Pro 5G Mobile Smartphone (8GB RAM + 128GB ROM)",
        "brand": "NovaTech Mobile",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Includes Handset, 67W Adapter, Type-C Cable, SIM Ejector)",
        "expected_mrp": "₹19,999",
        "manufacturer": "NovaTech Electronics Manufacturing Pvt Ltd",
        "manufacturer_address": "Ecotech 3, Greater Noida, Gautam Buddha Nagar, UP 201306",
        "packer": "NovaTech Electronics Manufacturing Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-888-NOVA, Email: service@novatech.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554402",
        "name": "VisionClear 43-inch 4K Ultra HD Smart Google LED TV",
        "brand": "VisionClear",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Screen Diagonal: 108 cm)",
        "expected_mrp": "₹27,990",
        "manufacturer": "VisionClear India Consumer Appliances Ltd",
        "manufacturer_address": "Electronic Hardware Park, Sri City, Tirupati District, AP 517646",
        "packer": "VisionClear India Consumer Appliances Ltd",
        "importer": None,
        "consumer_care_details": "Customer Support: 1800-999-VISION, Email: customercare@visionclear.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554403",
        "name": "BookPro 15.6-inch Intel Core i5 Laptop (16GB RAM / 512GB SSD)",
        "brand": "AeroComputing",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Screen Diagonal: 39.6 cm, Weight: 1.65 kg)",
        "expected_mrp": "₹54,990",
        "manufacturer": "AeroComputing Global Tech Ltd",
        "manufacturer_address": "Export Processing Zone, Penang, Malaysia",
        "packer": None,
        "importer": "AeroComputing Technology India Pvt Ltd, Whitefield, Bengaluru, Karnataka 560066",
        "consumer_care_details": "Helpline: 1800-300-AERO, Email: support.india@aerocomputing.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554404",
        "name": "SonicPods Active Noise Cancellation Wireless Earbuds",
        "brand": "SonicAudio",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (1 Pair Earbuds, 1 Charging Case, 1 USB Cable, 3 Pairs Ear Tips)",
        "expected_mrp": "₹2,499",
        "manufacturer": "Sonic Audio Devices India Pvt Ltd",
        "manufacturer_address": "C-45, Sector 63, Noida, Uttar Pradesh 201301",
        "packer": "Sonic Audio Devices India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Helpline: 0120-4444555, Email: wecare@sonicaudio.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554405",
        "name": "PowerVault 20000 mAh 22.5W Fast Charging Power Bank",
        "brand": "Voltaic Accessories",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Power Bank with Dual USB-A and Type-C Output)",
        "expected_mrp": "₹1,799",
        "manufacturer": "Voltaic Energy Solutions Ltd",
        "manufacturer_address": "Plot 88, Electronic City Phase 2, Bengaluru, Karnataka 560100",
        "packer": "Voltaic Energy Solutions Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 080-49998888, Email: care@voltaic.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554406",
        "name": "QuickBoil 1500W Stainless Steel Electric Kettle (1.8 Litre)",
        "brand": "KitchenPro",
        "category": "Home & Kitchen Appliances",
        "expected_net_quantity": "1 N (Capacity: 1.8 L)",
        "expected_mrp": "₹999",
        "manufacturer": "KitchenPro Home Appliances Ltd",
        "manufacturer_address": "Phase 3, Industrial Area, Baddi, Solan, Himachal Pradesh 173205",
        "packer": "KitchenPro Home Appliances Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-209-KITCH, Email: customercare@kitchenpro.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554407",
        "name": "GlideMaster 1250W Non-Stick Soleplate Steam Iron",
        "brand": "ThermoHome",
        "category": "Home & Kitchen Appliances",
        "expected_net_quantity": "1 N",
        "expected_mrp": "₹1,250",
        "manufacturer": "ThermoHome Electricals India Ltd",
        "manufacturer_address": "SIDCUL Industrial Area, Haridwar, Uttarakhand 249403",
        "packer": "ThermoHome Electricals India Ltd",
        "importer": None,
        "consumer_care_details": "Care Centre: 1800-103-IRON, Email: support@thermohome.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554408",
        "name": "AeroBreeze 1200 mm High Speed Decorative Ceiling Fan",
        "brand": "CoolAir Electricals",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "1 N (Blade Sweep: 1200 mm / 48 Inch)",
        "expected_mrp": "₹2,350",
        "manufacturer": "CoolAir Engineering India Ltd",
        "manufacturer_address": "14/5 Mathura Road, Faridabad, Haryana 121003",
        "packer": "CoolAir Engineering India Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-COOL, Email: contact@coolairelectricals.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554409",
        "name": "LuminaBright 9W B22 Cool Daylight LED Bulbs (Pack of 2)",
        "brand": "Lumina India",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "2 N",
        "expected_mrp": "₹180",
        "manufacturer": "Lumina Lighting Corporation India Ltd",
        "manufacturer_address": "Bhosari Industrial Estate, Pune, Maharashtra 411026",
        "packer": "Lumina Lighting Corporation India Ltd",
        "importer": None,
        "consumer_care_details": "Helpline: 020-67123456, Email: lumina.care@luminaindia.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907766554410",
        "name": "SurgeGuard 4-Way Universal Extension Board with 2M Cord",
        "brand": "Voltaic Accessories",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "1 N (Includes 4 Sockets, 4 Switches, 2-Metre Heavy Duty Cord)",
        "expected_mrp": "₹499",
        "manufacturer": "Voltaic Energy Solutions Ltd",
        "manufacturer_address": "Plot 88, Electronic City Phase 2, Bengaluru, Karnataka 560100",
        "packer": "Voltaic Energy Solutions Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 080-49998888, Email: care@voltaic.example.com",
        "is_demo": True
    },

    # --- 3. FOOD, STAPLES, BEVERAGES & SNACKS ---
    {
        "barcode": "8901234567890",
        "name": "DemoBakes Choco Delight Biscuits",
        "brand": "DemoBakes",
        "category": "Food & Beverages",
        "expected_net_quantity": "200 g",
        "expected_mrp": "₹50",
        "manufacturer": "Demo Packaged Goods India Pvt Ltd",
        "manufacturer_address": "Plot 42, Industrial Area, Andheri East, Mumbai, Maharashtra 400093",
        "packer": "Demo Packaged Goods India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-000-DEMO, Email: care@demobakes.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901719101037",
        "name": "Parle-G Original Gluco Biscuits",
        "brand": "Parle",
        "category": "Food & Beverages",
        "expected_net_quantity": "79 g",
        "expected_mrp": "₹10",
        "manufacturer": "Parle Products Private Limited",
        "manufacturer_address": "North Level Crossing, Vile Parle East, Mumbai, Maharashtra 400057",
        "packer": "Parle Products Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-222-753, Email: cs@parle.biz",
        "is_demo": True
    },
    {
        "barcode": "8909876543210",
        "name": "PureHarvest Refined Sunflower Oil",
        "brand": "PureHarvest",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹165",
        "manufacturer": "PureHarvest Agro Industries Ltd",
        "manufacturer_address": "Survey No. 108, Agro Corridor, Gandhinagar, Gujarat 382010",
        "packer": "PureHarvest Agro Industries Ltd",
        "importer": None,
        "consumer_care_details": "Customer Helpdesk: 079-00000000, Email: feedback@pureharvest.example.com",
        "is_demo": True
    },
    {
        "barcode": "8905544332211",
        "name": "Spiceland Royal Garam Masala Powder",
        "brand": "Spiceland",
        "category": "Food & Beverages",
        "expected_net_quantity": "100 g",
        "expected_mrp": "₹78",
        "manufacturer": "Spiceland Heritage Foods Co.",
        "manufacturer_address": "Sector 9, Spice Complex, Kochi, Kerala 682001",
        "packer": "Spiceland Heritage Foods Co.",
        "importer": None,
        "consumer_care_details": "Care Line: 0484-9999999, Email: spices@spiceland.example.com",
        "is_demo": True
    },
    {
        "barcode": "8907788990011",
        "name": "GoldenGrain Sharbati Whole Wheat Atta",
        "brand": "GoldenGrain",
        "category": "Food & Beverages",
        "expected_net_quantity": "5 kg",
        "expected_mrp": "₹260",
        "manufacturer": "GoldenGrain Mills Private Limited",
        "manufacturer_address": "Grain Market Road, Agri Hub, Indore, Madhya Pradesh 452001",
        "packer": "GoldenGrain Mills Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-222-GRAIN, Email: feedback@goldengrain.example.com",
        "is_demo": True
    },
    {
        "barcode": "8906677889900",
        "name": "AromaPeak Premium Instant Coffee",
        "brand": "AromaPeak",
        "category": "Food & Beverages",
        "expected_net_quantity": "50 g",
        "expected_mrp": "₹120",
        "manufacturer": "AromaPeak Plantation Beverages",
        "manufacturer_address": "Estate Rd 5, Hill Range, Chikmagalur, Karnataka 577101",
        "packer": "AromaPeak Plantation Beverages",
        "importer": None,
        "consumer_care_details": "Customer Service: 08262-888888, Email: coffee@aromapeak.example.com",
        "is_demo": True
    },
    {
        "barcode": "8904433221100",
        "name": "NutriBite California Roasted Almonds",
        "brand": "NutriBite",
        "category": "Food & Beverages",
        "expected_net_quantity": "250 g",
        "expected_mrp": "₹340",
        "manufacturer": "NutriBite Foodworks LLP",
        "manufacturer_address": "Plot 15, Food Park, Sonipat, Haryana 131029",
        "packer": "NutriBite Foodworks LLP",
        "importer": "Global Dryfruit Traders, New Delhi 110006",
        "consumer_care_details": "Toll Free: 1800-333-NUTR, Email: wecare@nutribite.example.com",
        "is_demo": True
    },
    {
        "barcode": "8903322110099",
        "name": "FreshOrchard 100% Mixed Fruit Juice",
        "brand": "FreshOrchard",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹130",
        "manufacturer": "FreshOrchard Beverage Bottlers",
        "manufacturer_address": "MIDC Phase 2, Industrial Zone, Pune, Maharashtra 411019",
        "packer": "FreshOrchard Beverage Bottlers",
        "importer": None,
        "consumer_care_details": "Customer Voice: 020-7777777, Email: service@freshorchard.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223301",
        "name": "Royal Feast Extra Long Aged Basmati Rice",
        "brand": "Heritage Grains",
        "category": "Food & Beverages",
        "expected_net_quantity": "5 kg",
        "expected_mrp": "₹590",
        "manufacturer": "Heritage Agro Foods Ltd",
        "manufacturer_address": "GT Road, Taraori, Karnal, Haryana 132116",
        "packer": "Heritage Agro Foods Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-180-RICE, Email: care@heritagegrains.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223302",
        "name": "SudhDhara Cold Pressed Kachi Ghani Mustard Oil",
        "brand": "SudhDhara",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹175",
        "manufacturer": "SudhDhara Oil Industries Ltd",
        "manufacturer_address": "Matsya Industrial Area, Alwar, Rajasthan 301030",
        "packer": "SudhDhara Oil Industries Ltd",
        "importer": None,
        "consumer_care_details": "Helpdesk: 0144-2881234, Email: feedback@sudhdhara.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223303",
        "name": "NatureFarm Unpolished Desi Toor Dal",
        "brand": "NatureFarm Organic",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 kg",
        "expected_mrp": "₹185",
        "manufacturer": "NatureFarm Agri Producer Co Ltd",
        "manufacturer_address": "MIDC Area, Latur, Maharashtra 413512",
        "packer": "NatureFarm Agri Producer Co Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-233-FARM, Email: organic@naturefarm.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223304",
        "name": "GauAmrit Pure Traditional Bilona Cow Ghee",
        "brand": "GauAmrit",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹680",
        "manufacturer": "GauAmrit Milk Products Ltd",
        "manufacturer_address": "Dairy Road, Anand, Gujarat 388001",
        "packer": "GauAmrit Milk Products Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 02692-245678, Email: care@gauamrit.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223305",
        "name": "ValleyPride Strong Assam CTC Black Tea",
        "brand": "ValleyPride",
        "category": "Food & Beverages",
        "expected_net_quantity": "500 g",
        "expected_mrp": "₹240",
        "manufacturer": "ValleyPride Tea Plantations Ltd",
        "manufacturer_address": "Tea Estate Rd, Dibrugarh, Assam 786001",
        "packer": "ValleyPride Tea Plantations Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-345-TEAS, Email: feedback@valleypride.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223306",
        "name": "ChocoArtisan 70% Intense Dark Chocolate Bar",
        "brand": "ChocoArtisan",
        "category": "Food & Beverages",
        "expected_net_quantity": "100 g",
        "expected_mrp": "₹150",
        "manufacturer": "ChocoArtisan Confectionery LLP",
        "manufacturer_address": "Botanical Garden Rd, Ooty, The Nilgiris, Tamil Nadu 643001",
        "packer": "ChocoArtisan Confectionery LLP",
        "importer": None,
        "consumer_care_details": "Customer Line: 0423-2441122, Email: care@chocoartisan.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223307",
        "name": "CrunchTime Tangy Tomato Potato Wafers",
        "brand": "CrunchTime",
        "category": "Food & Beverages",
        "expected_net_quantity": "78 g",
        "expected_mrp": "₹20",
        "manufacturer": "CrunchTime Foods India Ltd",
        "manufacturer_address": "Sector 3, Industrial Estate, Haridwar, Uttarakhand 249403",
        "packer": "CrunchTime Foods India Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-120-CHIP, Email: service@crunchtime.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223308",
        "name": "VitalMorning 100% Whole Grain Rolled Oats",
        "brand": "VitalMorning",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 kg",
        "expected_mrp": "₹225",
        "manufacturer": "VitalMorning Healthy Foods Pvt Ltd",
        "manufacturer_address": "Makarpura GIDC, Vadodara, Gujarat 390010",
        "packer": "VitalMorning Healthy Foods Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Helpline: 0265-2630000, Email: nutrition@vitalmorning.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223309",
        "name": "ForestPure 100% Raw Wild Forest Organic Honey",
        "brand": "ForestPure",
        "category": "Food & Beverages",
        "expected_net_quantity": "500 g",
        "expected_mrp": "₹270",
        "manufacturer": "ForestPure Apiaries India Pvt Ltd",
        "manufacturer_address": "Rajpur Road, Dehradun, Uttarakhand 248001",
        "packer": "ForestPure Apiaries India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-180-HONEY, Email: care@forestpure.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901112223310",
        "name": "OceanSalt Vacuum Evaporated Pure Iodised Salt",
        "brand": "OceanSalt",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 kg",
        "expected_mrp": "₹28",
        "manufacturer": "OceanSalt Marine Chemicals Ltd",
        "manufacturer_address": "Coastal Highway, Mithapur, Devbhumi Dwarka, Gujarat 361345",
        "packer": "OceanSalt Marine Chemicals Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 02892-234500, Email: feedback@oceansalt.example.com",
        "is_demo": True
    },

    # --- 4. PERSONAL CARE, COSMETICS & GROOMING ---
    {
        "barcode": "8901122334455",
        "name": "SparkleGlow Herbal Moisture Bathing Soap",
        "brand": "SparkleGlow",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "125 g",
        "expected_mrp": "₹45",
        "manufacturer": "Sparkle Personal Care Laboratories",
        "manufacturer_address": "Khasra 25, Pharma Park, Baddi, Himachal Pradesh 173205",
        "packer": "Sparkle Personal Care Laboratories",
        "importer": None,
        "consumer_care_details": "Helpline: 1800-111-GLOW, Email: support@sparkleglow.example.com",
        "is_demo": True
    },
    {
        "barcode": "8902233445501",
        "name": "SilkStrands Keratin Protein Repair Shampoo",
        "brand": "SilkStrands",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "400 ml",
        "expected_mrp": "₹399",
        "manufacturer": "SilkStrands Personal Care Laboratories Ltd",
        "manufacturer_address": "EPIP Industrial Zone, Baddi, Solan, HP 173205",
        "packer": "SilkStrands Personal Care Laboratories Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-456-HAIR, Email: care@silkstrands.example.com",
        "is_demo": True
    },
    {
        "barcode": "8902233445502",
        "name": "DentaShield 12-Hour Protection Herbal Toothpaste",
        "brand": "DentaShield",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "150 g",
        "expected_mrp": "₹95",
        "manufacturer": "DentaShield Healthcare Products Ltd",
        "manufacturer_address": "Gondpur Industrial Area, Paonta Sahib, Sirmour, HP 173025",
        "packer": "DentaShield Healthcare Products Ltd",
        "importer": None,
        "consumer_care_details": "Customer Line: 01704-223344, Email: support@dentashield.example.com",
        "is_demo": True
    },
    {
        "barcode": "8902233445503",
        "name": "SunGuard Ultra Matte Dry Touch Sunscreen SPF 50",
        "brand": "Dermacare",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "50 g",
        "expected_mrp": "₹449",
        "manufacturer": "Dermacare Formulations India Pvt Ltd",
        "manufacturer_address": "Sanand GIDC, Ahmedabad, Gujarat 382110",
        "packer": "Dermacare Formulations India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Helpdesk: 079-29701122, Email: care@dermacare.example.com",
        "is_demo": True
    },
    {
        "barcode": "8902233445504",
        "name": "CocoNourish 100% Pure Virgin Cold Pressed Coconut Oil",
        "brand": "CocoNourish",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "500 ml",
        "expected_mrp": "₹210",
        "manufacturer": "CocoNourish Agro Extracts Ltd",
        "manufacturer_address": "Kinfra Food Park, Kakkancherry, Malappuram, Kerala 673635",
        "packer": "CocoNourish Agro Extracts Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-COCO, Email: feedback@coconourish.example.com",
        "is_demo": True
    },
    {
        "barcode": "8902233445505",
        "name": "AeroScent Urban Musk No-Gas Perfumed Body Spray",
        "brand": "AeroScent",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "150 ml (100 g)",
        "expected_mrp": "₹250",
        "manufacturer": "AeroScent Aerosols India Ltd",
        "manufacturer_address": "GIDC Industrial Estate, Vapi, Valsad, Gujarat 396195",
        "packer": "AeroScent Aerosols India Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 0260-2430900, Email: contact@aeroscent.example.com",
        "is_demo": True
    },
    {
        "barcode": "8902233445506",
        "name": "PureGlow Gentle Foaming Vitamin C Face Wash",
        "brand": "PureGlow",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "100 ml",
        "expected_mrp": "₹249",
        "manufacturer": "Dermacare Formulations India Pvt Ltd",
        "manufacturer_address": "Sanand GIDC, Ahmedabad, Gujarat 382110",
        "packer": "Dermacare Formulations India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Helpdesk: 079-29701122, Email: care@pureglow.example.com",
        "is_demo": True
    },

    # --- 5. HOUSEHOLD CLEANING & HOME CARE ---
    {
        "barcode": "8903344556601",
        "name": "BrightWash Stain Defense Matic Laundry Detergent Powder",
        "brand": "BrightWash",
        "category": "Household & Cleaning",
        "expected_net_quantity": "2 kg",
        "expected_mrp": "₹375",
        "manufacturer": "BrightWash Consumer Products Ltd",
        "manufacturer_address": "Survey 74, Piparia Industrial Estate, Silvassa, DNH 396230",
        "packer": "BrightWash Consumer Products Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-WASH, Email: care@brightwash.example.com",
        "is_demo": True
    },
    {
        "barcode": "8903344556602",
        "name": "KleenShine Active Lemon Grease Cleaner Dishwash Gel",
        "brand": "KleenShine",
        "category": "Household & Cleaning",
        "expected_net_quantity": "500 ml",
        "expected_mrp": "₹115",
        "manufacturer": "KleenShine Chemical Industries Ltd",
        "manufacturer_address": "Wagle Industrial Estate, Thane West, Maharashtra 400604",
        "packer": "KleenShine Chemical Industries Ltd",
        "importer": None,
        "consumer_care_details": "Helpdesk: 022-25801122, Email: support@kleenshine.example.com",
        "is_demo": True
    },
    {
        "barcode": "8903344556603",
        "name": "GermKill 10x Citrus Disinfectant Surface & Floor Cleaner",
        "brand": "GermKill",
        "category": "Household & Cleaning",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹180",
        "manufacturer": "GermKill Hygiene Solutions Ltd",
        "manufacturer_address": "GIDC Chemical Zone, Jhagadia, Bharuch, Gujarat 393110",
        "packer": "GermKill Hygiene Solutions Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-200-GERM, Email: hygiene@germkill.example.com",
        "is_demo": True
    },
    {
        "barcode": "8903344556604",
        "name": "MosquitoShield Active Liquid Vaporizer Refill (Pack of 2)",
        "brand": "MosquitoShield",
        "category": "Household & Cleaning",
        "expected_net_quantity": "2 N (45 ml each, Total: 90 ml)",
        "expected_mrp": "₹160",
        "manufacturer": "PestControl Consumer Care Ltd",
        "manufacturer_address": "Kaloor Industrial Estate, Ernakulam, Kerala 682017",
        "packer": "PestControl Consumer Care Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-111-SHIELD, Email: care@pestcontrol.example.com",
        "is_demo": True
    },

    # --- 6. BABY CARE, HEALTHCARE & PHARMACEUTICALS ---
    {
        "barcode": "8904455667701",
        "name": "CareBaby Ultra Dry Comfort Diaper Pants (Large Size, 9-14 kg)",
        "brand": "CareBaby",
        "category": "Baby Care & Hygiene",
        "expected_net_quantity": "54 N",
        "expected_mrp": "₹899",
        "manufacturer": "CareBaby Hygiene Products India Pvt Ltd",
        "manufacturer_address": "SIPCOT Industrial Complex, Sriperumbudur, Tamil Nadu 602105",
        "packer": "CareBaby Hygiene Products India Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-300-BABY, Email: help@carebaby.example.com",
        "is_demo": True
    },
    {
        "barcode": "8904455667702",
        "name": "PureShield 70% Isopropyl Alcohol Instant Hand Sanitizer",
        "brand": "PureShield",
        "category": "Healthcare & Hygiene",
        "expected_net_quantity": "500 ml",
        "expected_mrp": "₹150",
        "manufacturer": "PureShield Healthcare Laboratories",
        "manufacturer_address": "Roorkee Industrial Corridor, Roorkee, Uttarakhand 247667",
        "packer": "PureShield Healthcare Laboratories",
        "importer": None,
        "consumer_care_details": "Helpline: 01332-267890, Email: service@pureshield.example.com",
        "is_demo": True
    },

    # --- 7. STATIONERY & OFFICE PRODUCTS ---
    {
        "barcode": "8904455667703",
        "name": "OfficePro 75 GSM High Brightness A4 Copier Paper",
        "brand": "OfficePro",
        "category": "Stationery & Office",
        "expected_net_quantity": "500 Sheets (Dimensions: 210 mm x 297 mm)",
        "expected_mrp": "₹340",
        "manufacturer": "OfficePro Paper Mills Ltd",
        "manufacturer_address": "Paper Town, Bhadravati, Shivamogga, Karnataka 577301",
        "packer": "OfficePro Paper Mills Ltd",
        "importer": None,
        "consumer_care_details": "Customer Care: 08282-265432, Email: care@officepro.example.com",
        "is_demo": True
    },
    {
        "barcode": "8904455667704",
        "name": "ClassMate Classic Hardbound Ruled A4 Notebook",
        "brand": "ClassMate",
        "category": "Stationery & Office",
        "expected_net_quantity": "1 N (192 Pages, Dimensions: 210 mm x 297 mm)",
        "expected_mrp": "₹120",
        "manufacturer": "ClassMate Stationery Manufacturing Ltd",
        "manufacturer_address": "Plot 7, Industrial Hub, Manesar, Gurugram, Haryana 122051",
        "packer": "ClassMate Stationery Manufacturing Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-NOTE, Email: service@classmate.example.com",
        "is_demo": True
    },
    {
        "barcode": "8901030012345",
        "name": "Tata Salt Vacuum Evaporated Iodized Salt",
        "brand": "Tata Salt",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 kg",
        "expected_mrp": "₹28.00 (incl. of all taxes)",
        "manufacturer": "Tata Consumer Products Limited",
        "manufacturer_address": "1, Bishop Lefroy Road, Kolkata, West Bengal 700020",
        "packer": "Tata Consumer Products Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-345-1720, Email: care@tataconsumer.com",
        "is_demo": True,
    },
    {
        "barcode": "8906007281017",
        "name": "Fortune Sunlite Refined Sunflower Oil Pouch",
        "brand": "Fortune",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 L / 910 g",
        "expected_mrp": "₹145.00 (incl. of all taxes)",
        "manufacturer": "Adani Wilmar Limited",
        "manufacturer_address": "Fortune House, Near Navrangpura Railway Crossing, Ahmedabad, Gujarat 380009",
        "packer": "Adani Wilmar Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-233-9999, Email: customercare@adaniwilmar.in",
        "is_demo": True,
    },
    {
        "barcode": "8901030825310",
        "name": "Maggi 2-Minute Masala Instant Noodles",
        "brand": "Maggi",
        "category": "Food & Beverages",
        "expected_net_quantity": "70 g",
        "expected_mrp": "₹14.00 (incl. of all taxes)",
        "manufacturer": "Nestle India Limited",
        "manufacturer_address": "100/101, World Trade Centre, Barakhamba Lane, New Delhi 110001",
        "packer": "Nestle India Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-103-1947, Email: wecare@in.nestle.com",
        "is_demo": True,
    },
    {
        "barcode": "8901063012876",
        "name": "Britannia Good Day Cashew Cookies",
        "brand": "Britannia",
        "category": "Food & Beverages",
        "expected_net_quantity": "200 g",
        "expected_mrp": "₹40.00 (incl. of all taxes)",
        "manufacturer": "Britannia Industries Limited",
        "manufacturer_address": "5/1A Hungerford Street, Kolkata, West Bengal 700017",
        "packer": "Britannia Industries Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-4449, Email: feedback@britindia.com",
        "is_demo": True,
    },
    {
        "barcode": "8901262010025",
        "name": "Amul Pasteurised Salted Butter",
        "brand": "Amul",
        "category": "Food & Beverages",
        "expected_net_quantity": "500 g",
        "expected_mrp": "₹275.00 (incl. of all taxes)",
        "manufacturer": "Gujarat Co-operative Milk Marketing Federation Ltd (GCMMF)",
        "manufacturer_address": "Amul Dairy Road, Anand, Gujarat 388001",
        "packer": "Gujarat Co-operative Milk Marketing Federation Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-258-3333, Email: customercare@amul.coop",
        "is_demo": True,
    },
    {
        "barcode": "8904004400018",
        "name": "Haldiram's Nagpur Aloo Bhujia Spiced Potato Sev",
        "brand": "Haldiram's",
        "category": "Food & Beverages",
        "expected_net_quantity": "400 g",
        "expected_mrp": "₹115.00 (incl. of all taxes)",
        "manufacturer": "Haldiram Foods International Pvt Ltd",
        "manufacturer_address": "Surya Nagar, Kalamna Road, Nagpur, Maharashtra 440035",
        "packer": "Haldiram Foods International Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Customer Care: 0712-2681122, Email: support@haldirams.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030383704",
        "name": "Brooke Bond Red Label Strong CTC Tea",
        "brand": "Red Label",
        "category": "Food & Beverages",
        "expected_net_quantity": "500 g",
        "expected_mrp": "₹280.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901058852661",
        "name": "Nescafe Classic 100% Pure Instant Coffee Glass Jar",
        "brand": "Nescafe",
        "category": "Food & Beverages",
        "expected_net_quantity": "100 g",
        "expected_mrp": "₹360.00 (incl. of all taxes)",
        "manufacturer": "Nestle India Limited",
        "manufacturer_address": "100/101, World Trade Centre, Barakhamba Lane, New Delhi 110001",
        "packer": "Nestle India Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-103-1947, Email: wecare@in.nestle.com",
        "is_demo": True,
    },
    {
        "barcode": "8901725181214",
        "name": "Everest Super Garam Masala Powder",
        "brand": "Everest",
        "category": "Food & Beverages",
        "expected_net_quantity": "100 g",
        "expected_mrp": "₹88.00 (incl. of all taxes)",
        "manufacturer": "S.Narendra Kumar & Co. (Everest Spices)",
        "manufacturer_address": "Everest House, 107/110, Dattani Plaza, Saki Naka, Andheri East, Mumbai 400072",
        "packer": "S.Narendra Kumar & Co.",
        "importer": None,
        "consumer_care_details": "Customer Care: 022-28504444, Email: customercare@everestspices.com",
        "is_demo": True,
    },
    {
        "barcode": "8901088001015",
        "name": "Saffola Gold Pro Healthy Lifestyle Blended Edible Oil",
        "brand": "Saffola",
        "category": "Food & Beverages",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹170.00 (incl. of all taxes)",
        "manufacturer": "Marico Limited",
        "manufacturer_address": "7th Floor, Grande Palladium, 175 CST Road, Kalina, Santacruz East, Mumbai 400098",
        "packer": "Marico Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-222-248, Email: ccc@marico.com",
        "is_demo": True,
    },
    {
        "barcode": "8901207040117",
        "name": "Cadbury Dairy Milk Silk Chocolate Bar",
        "brand": "Cadbury",
        "category": "Food & Beverages",
        "expected_net_quantity": "150 g",
        "expected_mrp": "₹175.00 (incl. of all taxes)",
        "manufacturer": "Mondelez India Foods Private Limited",
        "manufacturer_address": "Unit No. 2001, 20th Floor, Tower-3, Indiabulls Finance Centre, Parel, Mumbai 400013",
        "packer": "Mondelez India Foods Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-22-7080, Email: suggestions@mdlz.com",
        "is_demo": True,
    },
    {
        "barcode": "8901491101830",
        "name": "Lay's India's Magic Masala Potato Chips",
        "brand": "Lay's",
        "category": "Food & Beverages",
        "expected_net_quantity": "50 g",
        "expected_mrp": "₹20.00 (incl. of all taxes)",
        "manufacturer": "PepsiCo India Holdings Pvt Ltd",
        "manufacturer_address": "Level 3-6, Pioneer Square, Sector 62, Golf Course Ext Road, Gurugram, Haryana 122101",
        "packer": "PepsiCo India Holdings Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-224-020, Email: consumer.feedback@pepsico.com",
        "is_demo": True,
    },
    {
        "barcode": "8901491501029",
        "name": "Kurkure Masala Munch Crispy Snack",
        "brand": "Kurkure",
        "category": "Food & Beverages",
        "expected_net_quantity": "82 g",
        "expected_mrp": "₹20.00 (incl. of all taxes)",
        "manufacturer": "PepsiCo India Holdings Pvt Ltd",
        "manufacturer_address": "Level 3-6, Pioneer Square, Sector 62, Golf Course Ext Road, Gurugram, Haryana 122101",
        "packer": "PepsiCo India Holdings Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-224-020, Email: consumer.feedback@pepsico.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030704417",
        "name": "Kissan Fresh Tomato Ketchup Bottle",
        "brand": "Kissan",
        "category": "Food & Beverages",
        "expected_net_quantity": "950 g",
        "expected_mrp": "₹140.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901207038107",
        "name": "Bournvita Inner Strength Nutrition Drink Refill Pack",
        "brand": "Bournvita",
        "category": "Food & Beverages",
        "expected_net_quantity": "750 g",
        "expected_mrp": "₹340.00 (incl. of all taxes)",
        "manufacturer": "Mondelez India Foods Private Limited",
        "manufacturer_address": "Unit No. 2001, 20th Floor, Tower-3, Indiabulls Finance Centre, Parel, Mumbai 400013",
        "packer": "Mondelez India Foods Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-22-7080, Email: suggestions@mdlz.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030869109",
        "name": "Aashirvaad Superior MP Sharbati Whole Wheat Atta",
        "brand": "Aashirvaad",
        "category": "Food & Beverages",
        "expected_net_quantity": "5 kg",
        "expected_mrp": "₹310.00 (incl. of all taxes)",
        "manufacturer": "ITC Limited",
        "manufacturer_address": "Virginia House, 37 J.L. Nehru Road, Kolkata, West Bengal 700071",
        "packer": "ITC Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-4444, Email: itccares@itc.in",
        "is_demo": True,
    },
    {
        "barcode": "8901063032102",
        "name": "India Gate Feast Rozzana Basmati Rice Bag",
        "brand": "India Gate",
        "category": "Food & Beverages",
        "expected_net_quantity": "5 kg",
        "expected_mrp": "₹495.00 (incl. of all taxes)",
        "manufacturer": "KRBL Limited",
        "manufacturer_address": "5190, Lahori Gate, Delhi 110006",
        "packer": "KRBL Limited",
        "importer": None,
        "consumer_care_details": "Customer Care: 011-23968328, Email: customercare@krblindia.com",
        "is_demo": True,
    },
    {
        "barcode": "8901396388107",
        "name": "Dettol Original Germ Protection Bathing Soap (Pack of 4)",
        "brand": "Dettol",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "4 N (125 g each / 500 g total)",
        "expected_mrp": "₹210.00 (incl. of all taxes)",
        "manufacturer": "Reckitt Benckiser (India) Pvt Ltd",
        "manufacturer_address": "Plot No. 48, Institutional Area, Sector 32, Gurugram, Haryana 122001",
        "packer": "Reckitt Benckiser (India) Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-7245, Email: consumerhealth_india@reckitt.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030005019",
        "name": "Dove Cream Beauty Bathing Bar (Pack of 3)",
        "brand": "Dove",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "3 N (100 g each / 300 g total)",
        "expected_mrp": "₹225.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030018200",
        "name": "Pears Pure & Gentle Bathing Bar with Natural Glycerin",
        "brand": "Pears",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "125 g",
        "expected_mrp": "₹82.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901314010257",
        "name": "Colgate Strong Teeth Calcium Boost Dental Cream Toothpaste",
        "brand": "Colgate",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "200 g",
        "expected_mrp": "₹120.00 (incl. of all taxes)",
        "manufacturer": "Colgate-Palmolive (India) Limited",
        "manufacturer_address": "Colgate Research Centre, Main Street, Hiranandani Gardens, Powai, Mumbai 400076",
        "packer": "Colgate-Palmolive (India) Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-225599, Email: consumeraffairs_india@colpal.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030366622",
        "name": "Clinic Plus Strong & Long Health Shampoo with Milk Protein",
        "brand": "Clinic Plus",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "650 ml",
        "expected_mrp": "₹370.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901088012011",
        "name": "Parachute 100% Pure Coconut Hair Oil Flip-Top Bottle",
        "brand": "Parachute",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "500 ml",
        "expected_mrp": "₹190.00 (incl. of all taxes)",
        "manufacturer": "Marico Limited",
        "manufacturer_address": "7th Floor, Grande Palladium, 175 CST Road, Kalina, Santacruz East, Mumbai 400098",
        "packer": "Marico Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-222-248, Email: ccc@marico.com",
        "is_demo": True,
    },
    {
        "barcode": "8901138810015",
        "name": "Himalaya Purifying Neem Face Wash for Acne-Free Skin",
        "brand": "Himalaya",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "150 ml",
        "expected_mrp": "₹180.00 (incl. of all taxes)",
        "manufacturer": "The Himalaya Drug Company",
        "manufacturer_address": "Makali, Bengaluru, Karnataka 562162",
        "packer": "The Himalaya Drug Company",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-208-1930, Email: customer.service@himalayawellness.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030761205",
        "name": "Pond's Light Moisturiser Non-Oily Fresh Feel Cream",
        "brand": "Pond's",
        "category": "Personal Care & Cosmetics",
        "expected_net_quantity": "150 ml",
        "expected_mrp": "₹220.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030025116",
        "name": "Surf Excel Easy Wash Detergent Powder",
        "brand": "Surf Excel",
        "category": "Household & Cleaning",
        "expected_net_quantity": "1 kg",
        "expected_mrp": "₹140.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901396344103",
        "name": "Harpic Power Plus 10X Max Clean Toilet Cleaner Gel Original",
        "brand": "Harpic",
        "category": "Household & Cleaning",
        "expected_net_quantity": "1 L",
        "expected_mrp": "₹215.00 (incl. of all taxes)",
        "manufacturer": "Reckitt Benckiser (India) Pvt Ltd",
        "manufacturer_address": "Plot No. 48, Institutional Area, Sector 32, Gurugram, Haryana 122001",
        "packer": "Reckitt Benckiser (India) Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-7245, Email: consumerhealth_india@reckitt.com",
        "is_demo": True,
    },
    {
        "barcode": "8901396366013",
        "name": "Lizol Disinfectant Surface Floor Cleaner Citrus Fragrance",
        "brand": "Lizol",
        "category": "Household & Cleaning",
        "expected_net_quantity": "2 L",
        "expected_mrp": "₹385.00 (incl. of all taxes)",
        "manufacturer": "Reckitt Benckiser (India) Pvt Ltd",
        "manufacturer_address": "Plot No. 48, Institutional Area, Sector 32, Gurugram, Haryana 122001",
        "packer": "Reckitt Benckiser (India) Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-7245, Email: consumerhealth_india@reckitt.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030048122",
        "name": "Vim Dishwash Bar with Lemon Fragrance",
        "brand": "Vim",
        "category": "Household & Cleaning",
        "expected_net_quantity": "300 g",
        "expected_mrp": "₹30.00 (incl. of all taxes)",
        "manufacturer": "Hindustan Unilever Limited",
        "manufacturer_address": "Unilever House, B.D. Sawant Marg, Chakala, Andheri East, Mumbai 400099",
        "packer": "Hindustan Unilever Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-10-22-221, Email: lever.care@unilever.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030049556",
        "name": "Colin Glass and Multi-Surface Cleaner Spray",
        "brand": "Colin",
        "category": "Household & Cleaning",
        "expected_net_quantity": "500 ml",
        "expected_mrp": "₹110.00 (incl. of all taxes)",
        "manufacturer": "Reckitt Benckiser (India) Pvt Ltd",
        "manufacturer_address": "Plot No. 48, Institutional Area, Sector 32, Gurugram, Haryana 122001",
        "packer": "Reckitt Benckiser (India) Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-7245, Email: consumerhealth_india@reckitt.com",
        "is_demo": True,
    },
    {
        "barcode": "8901023010118",
        "name": "Good Knight Gold Flash Liquid Mosquito Vaporizer Refill",
        "brand": "Good Knight",
        "category": "Household & Cleaning",
        "expected_net_quantity": "45 ml",
        "expected_mrp": "₹85.00 (incl. of all taxes)",
        "manufacturer": "Godrej Consumer Products Limited",
        "manufacturer_address": "Godrej One, 4th Floor, Pirojshanagar, Eastern Express Highway, Vikhroli East, Mumbai 400079",
        "packer": "Godrej Consumer Products Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-266-0007, Email: care@godrejcp.com",
        "is_demo": True,
    },
    {
        "barcode": "8901314050116",
        "name": "Pampers All Round Protection Pants Diaper (Medium, 72 Count)",
        "brand": "Pampers",
        "category": "Baby Care & Hygiene",
        "expected_net_quantity": "72 N (Size: Medium, 7 - 12 kg)",
        "expected_mrp": "₹1,099.00 (incl. of all taxes)",
        "manufacturer": "Procter & Gamble Home Products Pvt Ltd",
        "manufacturer_address": "P&G Plaza, Cardinal Gracias Road, Chakala, Andheri East, Mumbai 400099",
        "packer": "Procter & Gamble Home Products Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-202-1364, Email: consumer_care.im@pg.com",
        "is_demo": True,
    },
    {
        "barcode": "8901052020112",
        "name": "Johnson's Baby Bathing Soap with Natural Milk & Rice",
        "brand": "Johnson's",
        "category": "Baby Care & Hygiene",
        "expected_net_quantity": "150 g",
        "expected_mrp": "₹95.00 (incl. of all taxes)",
        "manufacturer": "Johnson & Johnson Private Limited",
        "manufacturer_address": "501 Arena Space, Behind Majas Bus Depot, Off JVLR, Jogeshwari East, Mumbai 400060",
        "packer": "Johnson & Johnson Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-228-111, Email: care@jnjindia.com",
        "is_demo": True,
    },
    {
        "barcode": "8901058860017",
        "name": "Nestle Cerelac Fortified Baby Cereal with Milk Wheat-Apple",
        "brand": "Cerelac",
        "category": "Baby Care & Hygiene",
        "expected_net_quantity": "300 g",
        "expected_mrp": "₹285.00 (incl. of all taxes)",
        "manufacturer": "Nestle India Limited",
        "manufacturer_address": "100/101, World Trade Centre, Barakhamba Lane, New Delhi 110001",
        "packer": "Nestle India Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-103-1947, Email: wecare@in.nestle.com",
        "is_demo": True,
    },
    {
        "barcode": "8906087770114",
        "name": "Mother Sparsh 99% Pure Water Unscented Baby Wipes (72 Wipes)",
        "brand": "Mother Sparsh",
        "category": "Baby Care & Hygiene",
        "expected_net_quantity": "72 N (Dimensions: 15 cm x 20 cm)",
        "expected_mrp": "₹299.00 (incl. of all taxes)",
        "manufacturer": "Mother Sparsh Baby Care Pvt Ltd",
        "manufacturer_address": "Plot No. 330, Phase 2, Industrial Area, Panchkula, Haryana 134113",
        "packer": "Mother Sparsh Baby Care Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Customer Care: 0172-5060444, Email: care@mothersparsh.com",
        "is_demo": True,
    },
    {
        "barcode": "8901396311013",
        "name": "Dettol Antiseptic Disinfectant Liquid 550ml",
        "brand": "Dettol",
        "category": "Healthcare & Hygiene",
        "expected_net_quantity": "550 ml",
        "expected_mrp": "₹210.00 (incl. of all taxes)",
        "manufacturer": "Reckitt Benckiser (India) Pvt Ltd",
        "manufacturer_address": "Plot No. 48, Institutional Area, Sector 32, Gurugram, Haryana 122001",
        "packer": "Reckitt Benckiser (India) Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-7245, Email: consumerhealth_india@reckitt.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030060018",
        "name": "Vicks VapoRub Cold & Cough Relief Balm Container",
        "brand": "Vicks",
        "category": "Healthcare & Hygiene",
        "expected_net_quantity": "50 ml",
        "expected_mrp": "₹155.00 (incl. of all taxes)",
        "manufacturer": "Procter & Gamble Hygiene and Health Care Ltd",
        "manufacturer_address": "P&G Plaza, Cardinal Gracias Road, Chakala, Andheri East, Mumbai 400099",
        "packer": "Procter & Gamble Hygiene and Health Care Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-202-1364, Email: consumer_care.im@pg.com",
        "is_demo": True,
    },
    {
        "barcode": "8901396399011",
        "name": "Moov Fast Pain Relief Herbal Spray Can",
        "brand": "Moov",
        "category": "Healthcare & Hygiene",
        "expected_net_quantity": "50 g / 59 ml",
        "expected_mrp": "₹185.00 (incl. of all taxes)",
        "manufacturer": "Reckitt Benckiser (India) Pvt Ltd",
        "manufacturer_address": "Plot No. 48, Institutional Area, Sector 32, Gurugram, Haryana 122001",
        "packer": "Reckitt Benckiser (India) Pvt Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-7245, Email: consumerhealth_india@reckitt.com",
        "is_demo": True,
    },
    {
        "barcode": "8901207011025",
        "name": "Eno Fruit Salt Regular Fast Acidity Relief Bottle",
        "brand": "Eno",
        "category": "Healthcare & Hygiene",
        "expected_net_quantity": "100 g",
        "expected_mrp": "₹160.00 (incl. of all taxes)",
        "manufacturer": "GlaxoSmithKline Consumer Healthcare (Haleon India)",
        "manufacturer_address": "Patiala Road, Nabha, Punjab 147201",
        "packer": "GlaxoSmithKline Consumer Healthcare",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-22-2211, Email: consumerfeedback@haleon.com",
        "is_demo": True,
    },
    {
        "barcode": "8901207012305",
        "name": "Dabur Chyawanprash 2X Immunity Booster Awaleha",
        "brand": "Dabur",
        "category": "Healthcare & Hygiene",
        "expected_net_quantity": "1 kg",
        "expected_mrp": "₹395.00 (incl. of all taxes)",
        "manufacturer": "Dabur India Limited",
        "manufacturer_address": "8/3, Asaf Ali Road, New Delhi 110002",
        "packer": "Dabur India Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-103-1644, Email: daburcares@feedback.dabur",
        "is_demo": True,
    },
    {
        "barcode": "8904130865510",
        "name": "boAt Airdopes 141 True Wireless Earbuds with 42H Playtime",
        "brand": "boAt",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Includes 1 Pair Earbuds, Charging Case, Type-C Cable, Extra Eartips)",
        "expected_mrp": "₹4,490.00 (incl. of all taxes)",
        "manufacturer": "Imagine Marketing Limited (boAt)",
        "manufacturer_address": "Unit No. 201 & 202, D-Wing, Corporate Avenue, Andheri Ghatkopar Link Road, Mumbai 400093",
        "packer": "Imagine Marketing Limited",
        "importer": None,
        "consumer_care_details": "Customer Care: 022-6918-1920, Email: info@imaginemarketingindia.com",
        "is_demo": True,
    },
    {
        "barcode": "8904130861123",
        "name": "boAt Bassheads 100 Wired in-Ear Earphones with Mic",
        "brand": "boAt",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Cord Length: 1.2 m)",
        "expected_mrp": "₹999.00 (incl. of all taxes)",
        "manufacturer": "Imagine Marketing Limited (boAt)",
        "manufacturer_address": "Unit No. 201 & 202, D-Wing, Corporate Avenue, Andheri Ghatkopar Link Road, Mumbai 400093",
        "packer": "Imagine Marketing Limited",
        "importer": None,
        "consumer_care_details": "Customer Care: 022-6918-1920, Email: info@imaginemarketingindia.com",
        "is_demo": True,
    },
    {
        "barcode": "8906120101114",
        "name": "Noise ColorFit Pulse 2 Max 1.85-inch Display Bluetooth Calling Smartwatch",
        "brand": "Noise",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Includes Smartwatch, Magnetic Charger, User Manual)",
        "expected_mrp": "₹5,999.00 (incl. of all taxes)",
        "manufacturer": "Nexxbase Marketing Private Limited",
        "manufacturer_address": "Khasra No. 146/25/2/1, Jail Road, Badshahpur, Gurugram, Haryana 122101",
        "packer": "Nexxbase Marketing Private Limited",
        "importer": None,
        "consumer_care_details": "Helpdesk: 08882-132-132, Email: help@nexxbase.com",
        "is_demo": True,
    },
    {
        "barcode": "8906100203332",
        "name": "Mi 20000mAh 18W Fast Charging Power Bank 3i",
        "brand": "Mi",
        "category": "Consumer Electronics",
        "expected_net_quantity": "1 N (Capacity: 20000mAh 74Wh 3.7V)",
        "expected_mrp": "₹2,199.00 (incl. of all taxes)",
        "manufacturer": "Xiaomi Technology India Private Limited",
        "manufacturer_address": "Building Orchid, Block E, Embassy Tech Village, Outer Ring Road, Bengaluru, Karnataka 560103",
        "packer": "Xiaomi Technology India Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-103-6286, Email: service.in@xiaomi.com",
        "is_demo": True,
    },
    {
        "barcode": "8901365123011",
        "name": "Prestige Iris 750W Mixer Grinder with 3 Stainless Steel Jars",
        "brand": "Prestige",
        "category": "Home & Kitchen Appliances",
        "expected_net_quantity": "1 N (Includes 750W Motor Unit, 1.5L Wet Jar, 1.0L Dry Jar, 300ml Chutney Jar)",
        "expected_mrp": "₹3,995.00 (incl. of all taxes)",
        "manufacturer": "TTK Prestige Limited",
        "manufacturer_address": "11th Floor, Brigade Towers, 135 Brigade Road, Bengaluru, Karnataka 560025",
        "packer": "TTK Prestige Limited",
        "importer": None,
        "consumer_care_details": "Customer Voice: 080-6900-5555, Email: customercare@ttkprestige.com",
        "is_demo": True,
    },
    {
        "barcode": "8901235678901",
        "name": "Bajaj DX 7 1000W Lightweight Dry Iron Non-Stick Golden Soleplate",
        "brand": "Bajaj",
        "category": "Home & Kitchen Appliances",
        "expected_net_quantity": "1 N (Wattage: 1000 W)",
        "expected_mrp": "₹1,150.00 (incl. of all taxes)",
        "manufacturer": "Bajaj Electricals Limited",
        "manufacturer_address": "45/47, Veer Nariman Road, Fort, Mumbai, Maharashtra 400001",
        "packer": "Bajaj Electricals Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-5963, Email: consumercare@bajajelectricals.com",
        "is_demo": True,
    },
    {
        "barcode": "8901030991121",
        "name": "Philips HD9306 1.5-Litre Electric Kettle Food-Grade Stainless Steel",
        "brand": "Philips",
        "category": "Home & Kitchen Appliances",
        "expected_net_quantity": "1 N (Volume Capacity: 1.5 L, 1800 W)",
        "expected_mrp": "₹2,695.00 (incl. of all taxes)",
        "manufacturer": "Philips Domestic Appliances India Ltd",
        "manufacturer_address": "DLF Cyber City, Tower A, 8th Floor, Phase 2, Gurugram, Haryana 122002",
        "packer": "Philips Domestic Appliances India Ltd",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-2929, Email: customercare.india@philips.com",
        "is_demo": True,
    },
    {
        "barcode": "8901412010115",
        "name": "Crompton Arno Neo 15-Litre 5-Star Storage Water Geyser",
        "brand": "Crompton",
        "category": "Home & Kitchen Appliances",
        "expected_net_quantity": "1 N (Tank Capacity: 15 L, 2000 W)",
        "expected_mrp": "₹7,999.00 (incl. of all taxes)",
        "manufacturer": "Crompton Greaves Consumer Electricals Limited",
        "manufacturer_address": "Equinox Business Park, Tower 3, 1st Floor, LBS Marg, Kurla West, Mumbai 400070",
        "packer": "Crompton Greaves Consumer Electricals Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-419-0505, Email: consumer.support@crompton.co.in",
        "is_demo": True,
    },
    {
        "barcode": "8901030987654",
        "name": "Philips Stellar Bright 9W B22 Cool Day White LED Bulb (Pack of 2)",
        "brand": "Philips",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "2 N (Luminous Flux: 900 Lumens each, Base: B22)",
        "expected_mrp": "₹240.00 (incl. of all taxes)",
        "manufacturer": "Signify Innovations India Limited (Formerly Philips Lighting)",
        "manufacturer_address": "PS Arcade, 9th Floor, Golf Course Road, Sector 42, Gurugram, Haryana 122002",
        "packer": "Signify Innovations India Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-102-5963, Email: lighting.india@signify.com",
        "is_demo": True,
    },
    {
        "barcode": "8901305010012",
        "name": "Wipro Garnet 12W Concealed LED Downlight Round Cool White",
        "brand": "Wipro",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "1 N (1080 Lumens, Cutout: 120 mm)",
        "expected_mrp": "₹450.00 (incl. of all taxes)",
        "manufacturer": "Wipro Enterprises Private Limited",
        "manufacturer_address": "C Block, CCLG Division, Doddakannelli, Sarjapur Road, Bengaluru, Karnataka 560035",
        "packer": "Wipro Enterprises Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-1969, Email: feedback.wiproconsumer@wipro.com",
        "is_demo": True,
    },
    {
        "barcode": "8901234990011",
        "name": "Havells Crabtree Athena 6A 1-Way Modular Switch White (Pack of 10)",
        "brand": "Havells",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "10 N (Current Rating: 6A, 240V~)",
        "expected_mrp": "₹650.00 (incl. of all taxes)",
        "manufacturer": "Havells India Limited",
        "manufacturer_address": "QRG Towers, 2D, Expressway, Sector 126, Noida, Uttar Pradesh 201304",
        "packer": "Havells India Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-103-1313, Email: customercare@havells.com",
        "is_demo": True,
    },
    {
        "barcode": "8902030010114",
        "name": "Polycab 1.5 sq mm Flame Retardant Single Core Copper Wire (90m Coil)",
        "brand": "Polycab",
        "category": "Electricals & Lighting",
        "expected_net_quantity": "1 N (Length: 90 m, Conductor Area: 1.5 sq mm)",
        "expected_mrp": "₹2,150.00 (incl. of all taxes)",
        "manufacturer": "Polycab India Limited",
        "manufacturer_address": "Polycab House, 771, Mogul Lane, Mahim West, Mumbai, Maharashtra 400016",
        "packer": "Polycab India Limited",
        "importer": None,
        "consumer_care_details": "Customer Care: 022-67351400, Email: customercare@polycab.com",
        "is_demo": True,
    },
    {
        "barcode": "8908877665511",
        "name": "Raymond Home 100% Cotton 500 GSM Bath Towel 70x140 cm",
        "brand": "Raymond Home",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Dimensions: 70 cm x 140 cm)",
        "expected_mrp": "₹699.00 (incl. of all taxes)",
        "manufacturer": "Raymond Consumer Care Limited",
        "manufacturer_address": "Pokhran Road No. 1, Jekegram, Thane West, Maharashtra 400606",
        "packer": "Raymond Consumer Care Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-222-777, Email: raymondhomecare@raymond.in",
        "is_demo": True,
    },
    {
        "barcode": "8908877665512",
        "name": "Bombay Dyeing Floral Pure Cotton Double Bedsheet with 2 Pillow Covers",
        "brand": "Bombay Dyeing",
        "category": "Bedding & Textiles",
        "expected_net_quantity": "1 N (Bedsheet: 220 cm x 240 cm, 2 Pillow Covers: 46 cm x 69 cm)",
        "expected_mrp": "₹1,199.00 (incl. of all taxes)",
        "manufacturer": "The Bombay Dyeing and Manufacturing Co. Ltd",
        "manufacturer_address": "Neville House, J.N. Heredia Marg, Ballard Estate, Mumbai 400001",
        "packer": "The Bombay Dyeing and Manufacturing Co. Ltd",
        "importer": None,
        "consumer_care_details": "Customer Voice: 022-66600000, Email: retailcustomercare@bombaydyeing.com",
        "is_demo": True,
    },
    {
        "barcode": "8901057010114",
        "name": "Reynolds 045 Fine Carbure Blue Ballpoint Pen (Pack of 10)",
        "brand": "Reynolds",
        "category": "Stationery & Office",
        "expected_net_quantity": "10 N (Tip Size: 0.7 mm, Ink: Blue)",
        "expected_mrp": "₹100.00 (incl. of all taxes)",
        "manufacturer": "Reynolds Pens India Private Limited",
        "manufacturer_address": "Plot No. 15, SIPCOT Industrial Complex, Gummidipoondi, Tamil Nadu 601201",
        "packer": "Reynolds Pens India Private Limited",
        "importer": None,
        "consumer_care_details": "Customer Care: 044-27922222, Email: reynoldscare@newellco.com",
        "is_demo": True,
    },
    {
        "barcode": "8901057020229",
        "name": "Cello Butterflow Classic Roller Ball Pen Pack of 5 Blue",
        "brand": "Cello",
        "category": "Stationery & Office",
        "expected_net_quantity": "5 N (Tip Size: 0.7 mm, Swiss Tip)",
        "expected_mrp": "₹50.00 (incl. of all taxes)",
        "manufacturer": "BIC Cello India Private Limited",
        "manufacturer_address": "Cello House, Corporate Avenue, Sonawala Road, Goregaon East, Mumbai 400063",
        "packer": "BIC Cello India Private Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-22-2250, Email: cello.support@bicworld.com",
        "is_demo": True,
    },
    {
        "barcode": "8901236010019",
        "name": "Classmate Pulse Spiral Bound 300 Pages Single Line Notebook",
        "brand": "Classmate",
        "category": "Stationery & Office",
        "expected_net_quantity": "1 N (300 Pages, Dimensions: 24.0 cm x 18.0 cm)",
        "expected_mrp": "₹165.00 (incl. of all taxes)",
        "manufacturer": "ITC Limited (Education & Stationery Products Business)",
        "manufacturer_address": "ITC Green Centre, 10, ESPB, Banaswadi Main Road, Bengaluru, Karnataka 560005",
        "packer": "ITC Limited",
        "importer": None,
        "consumer_care_details": "Toll Free: 1800-425-4444, Email: classmate@itc.in",
        "is_demo": True,
    },
    {
        "barcode": "8901198010013",
        "name": "Faber-Castell 24 Triangular Colour Pencils with Sharpener",
        "brand": "Faber-Castell",
        "category": "Stationery & Office",
        "expected_net_quantity": "24 N (Includes 24 Hexagonal/Triangular Pencils + 1 Sharpener)",
        "expected_mrp": "₹150.00 (incl. of all taxes)",
        "manufacturer": "A.W. Faber-Castell (India) Private Limited",
        "manufacturer_address": "801, Kamla Executive Park, J.B. Nagar, Andheri East, Mumbai 400059",
        "packer": "A.W. Faber-Castell (India) Private Limited",
        "importer": None,
        "consumer_care_details": "Helpdesk: 022-67729100, Email: info@faber-castell.co.in",
        "is_demo": True,
    },
    {
        "barcode": "8901057030334",
        "name": "Camlin Kokuyo Artist Acrylic Colour 12 Shades Box (12 Tubes x 9ml)",
        "brand": "Camel",
        "category": "Stationery & Office",
        "expected_net_quantity": "12 N (12 Tubes x 9 ml each / 108 ml total)",
        "expected_mrp": "₹280.00 (incl. of all taxes)",
        "manufacturer": "Kokuyo Camlin Limited",
        "manufacturer_address": "48/2, Hilton House, Central Road, MIDC, Andheri East, Mumbai 400093",
        "packer": "Kokuyo Camlin Limited",
        "importer": None,
        "consumer_care_details": "Customer Care: 022-66557007, Email: support@kokuyocamlin.com",
        "is_demo": True,
    },
    {
        "barcode": "8904001201011",
        "name": "Kangaro HP-45 Heavy Duty Plier Metal Stapler",
        "brand": "Kangaro",
        "category": "Stationery & Office",
        "expected_net_quantity": "1 N (Stapling Capacity: 30 Sheets, Compatible with 24/6 & 26/6 Staples)",
        "expected_mrp": "₹260.00 (incl. of all taxes)",
        "manufacturer": "Kangaro Industries Limited",
        "manufacturer_address": "B-XXX-6754, Focal Point, Ludhiana, Punjab 141010",
        "packer": "Kangaro Industries Limited",
        "importer": None,
        "consumer_care_details": "Helpdesk: 0161-2674901, Email: sales@kangaro.com",
        "is_demo": True,
    },
]


class ProductService:
    @staticmethod
    def seed_demo_products(db: Session) -> int:
        """
        Upsert all standard reference products into the database.
        Ensures any new products in DEMO_PRODUCTS are inserted even if the DB is already initialized.
        """
        seeded = 0
        for item in DEMO_PRODUCTS:
            existing = db.query(Product).filter(Product.barcode == item["barcode"]).first()
            if not existing:
                product = Product(**item)
                db.add(product)
                seeded += 1
            else:
                # Update baseline attributes if needed
                for key, val in item.items():
                    setattr(existing, key, val)
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
        """Look up product by internal database ID."""
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def list_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Product]:
        """List reference/demo products with optional category and search filters."""
        query = db.query(Product)
        if category and category != "ALL":
            query = query.filter(Product.category == category)
        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                (Product.name.ilike(s)) |
                (Product.barcode.ilike(s)) |
                (Product.brand.ilike(s)) |
                (Product.category.ilike(s))
            )
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> Product:
        """Register a new product in the reference database."""
        product = Product(**product_in.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def upsert_inspected_product(
        db: Session,
        scan_id: str,
        barcode: Optional[str],
        extracted_fields: Any,
        category_hint: Optional[str] = None
    ) -> Optional[Product]:
        """
        Auto-saves every inspected product into the database reference catalog.
        - If barcode already exists in DB, updates any missing attributes and links to scan.
        - If product does not exist, registers a new Product entry (is_demo=False).
        - Links scan.product_id = product.id and commits.
        """
        from app.models.scan import Scan

        if not scan_id:
            return None

        # Convert extracted_fields list or dict to simple lookup dict
        fields_dict: Dict[str, str] = {}
        if isinstance(extracted_fields, list):
            for item in extracted_fields:
                if hasattr(item, "field_name") and hasattr(item, "value"):
                    fields_dict[item.field_name] = str(item.value or "").strip()
                elif isinstance(item, dict):
                    fields_dict[item.get("field_name", "")] = str(item.get("value", "")).strip()
        elif isinstance(extracted_fields, dict):
            for k, v in extracted_fields.items():
                if isinstance(v, dict):
                    fields_dict[k] = str(v.get("value", "")).strip()
                elif hasattr(v, "value"):
                    fields_dict[k] = str(v.value or "").strip()
                elif isinstance(v, str):
                    fields_dict[k] = v.strip()

        scan = db.query(Scan).filter(Scan.id == scan_id).first()

        clean_barcode = (barcode or (scan.barcode if scan else "") or "").strip()
        if not clean_barcode:
            clean_barcode = f"INSP-{scan_id[:12].upper()}"

        # Check existing product by barcode
        product = db.query(Product).filter(Product.barcode == clean_barcode).first()

        name = fields_dict.get("product_name") or (f"Inspected Commodity ({clean_barcode})" if clean_barcode else "Inspected Packaging Commodity")
        net_qty = fields_dict.get("net_quantity") or "Declared on package"
        mrp = fields_dict.get("mrp") or "Declared on package"
        mfg = fields_dict.get("manufacturer_name_and_address") or "Declared on package"
        consumer_care = fields_dict.get("consumer_care") or "Declared on package"

        # Derive brand
        brand = "Generic"
        if name and not name.startswith("Inspected"):
            parts = name.split()
            if len(parts) > 0 and len(parts[0]) >= 2:
                brand = parts[0]

        # Derive category
        cat = category_hint or "Packaged Commodity"
        name_lower = name.lower()
        if any(w in name_lower for w in ["tea", "coffee", "biscuit", "cookie", "flour", "atta", "salt", "oil", "noodle", "snack", "chips", "juice", "butter", "milk", "bhujia", "rice", "dal"]):
            cat = "Food & Beverages"
        elif any(w in name_lower for w in ["soap", "shampoo", "toothpaste", "lotion", "cream", "moisturiser", "hair oil", "wash", "face"]):
            cat = "Personal Care & Cosmetics"
        elif any(w in name_lower for w in ["detergent", "cleaner", "dishwash", "liquid", "floor", "toilet", "wash", "mosquito"]):
            cat = "Household & Cleaning"
        elif any(w in name_lower for w in ["diaper", "baby", "wipes", "cereal"]):
            cat = "Baby Care & Hygiene"
        elif any(w in name_lower for w in ["balm", "syrup", "antiseptic", "ointment", "pain", "relief", "chyawanprash"]):
            cat = "Healthcare & Hygiene"
        elif any(w in name_lower for w in ["earbuds", "headphone", "mobile", "smartwatch", "charger", "tv", "speaker", "power bank"]):
            cat = "Consumer Electronics"
        elif any(w in name_lower for w in ["grinder", "kettle", "iron", "cooktop", "heater", "purifier"]):
            cat = "Home & Kitchen Appliances"
        elif any(w in name_lower for w in ["bulb", "led", "wire", "switch", "socket", "fan"]):
            cat = "Electricals & Lighting"
        elif any(w in name_lower for w in ["bedsheet", "towel", "curtain", "dohar", "cushion"]):
            cat = "Bedding & Textiles"
        elif any(w in name_lower for w in ["notebook", "pen", "pencil", "stapler", "paper"]):
            cat = "Stationery & Office"

        if not product:
            product = Product(
                barcode=clean_barcode,
                name=name[:255],
                brand=brand[:255],
                category=cat[:255],
                expected_net_quantity=net_qty[:512],
                expected_mrp=mrp[:128],
                manufacturer=mfg[:255],
                manufacturer_address=mfg[:1024],
                packer=mfg[:255],
                importer=None,
                consumer_care_details=consumer_care[:1024],
                is_demo=False
            )
            db.add(product)
            db.flush()
        else:
            # Update fields if current record has defaults and new inspection found better values
            if fields_dict.get("product_name") and "Inspected" in product.name:
                product.name = fields_dict["product_name"][:255]
            if fields_dict.get("net_quantity") and product.expected_net_quantity == "Declared on package":
                product.expected_net_quantity = fields_dict["net_quantity"][:512]
            if fields_dict.get("mrp") and product.expected_mrp == "Declared on package":
                product.expected_mrp = fields_dict["mrp"][:128]
            if fields_dict.get("manufacturer_name_and_address") and product.manufacturer == "Declared on package":
                product.manufacturer = fields_dict["manufacturer_name_and_address"][:255]
                product.manufacturer_address = fields_dict["manufacturer_name_and_address"][:1024]
            if fields_dict.get("consumer_care") and product.consumer_care_details == "Declared on package":
                product.consumer_care_details = fields_dict["consumer_care"][:1024]

        if scan:
            scan.product_id = product.id
            if not scan.barcode:
                scan.barcode = clean_barcode

        db.commit()
        db.refresh(product)
        return product
