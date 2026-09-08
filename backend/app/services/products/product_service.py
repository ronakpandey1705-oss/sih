from typing import Optional, List
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
    }
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
