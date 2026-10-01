"""
Phase 5 - Synthetic Indian invoices ka "data" hissa: item catalog, vendor
naam, GSTIN/HSN generators. Koi image/rendering logic yahan nahi - sirf
random-but-realistic values banate hain.

KYUN Faker nahi use kiya (jabki master plan me likha tha): Faker ka en_IN
locale generic filler deta hai (random company names), asli Indian retail
items/HSN codes nahi jaanta. Hand-written catalog zyada control deta hai
aur ek extra dependency (Faker install + verify) bhi nahi chahiye - "avoid
over-engineering" wale principle se yahi better choice hai.
"""
import random
import string

# (item name, HSN code, price range in Rs)
ITEM_CATALOG = [
    # Groceries
    ("Basmati Rice 5kg", "1006", (350, 650)),
    ("Wheat Flour 5kg", "1101", (180, 280)),
    ("Sugar 1kg", "1701", (40, 60)),
    ("Tea Powder 250g", "0902", (90, 180)),
    ("Sunflower Oil 1L", "1507", (140, 220)),
    ("Toor Dal 1kg", "0713", (120, 180)),
    ("Salt 1kg", "2501", (18, 28)),
    ("Basmati Rice 1kg", "1006", (80, 140)),
    ("Coffee Powder 200g", "0901", (110, 220)),
    ("Milk Powder 500g", "0402", (220, 380)),
    # Electronics
    ("Mobile Phone", "8517", (8000, 25000)),
    ("Bluetooth Earphones", "8518", (600, 2500)),
    ("Mobile Charger", "8504", (250, 900)),
    ("USB Cable", "8544", (99, 349)),
    ("Power Bank 10000mAh", "8507", (799, 1999)),
    ("LED Bulb 9W", "8539", (60, 150)),
    ("Extension Board", "8536", (250, 700)),
    # Stationery
    ("Notebook 200pg", "4820", (40, 90)),
    ("Ball Pen (Pack of 5)", "9608", (25, 60)),
    ("Pencil Box Set", "9609", (30, 80)),
    ("A4 Paper Ream", "4802", (220, 320)),
    ("Geometry Box", "9017", (60, 150)),
    ("File Folder", "4820", (20, 50)),
    # Apparel
    ("Cotton T-Shirt", "6109", (350, 799)),
    ("Formal Shirt", "6205", (599, 1499)),
    ("Denim Jeans", "6203", (899, 2199)),
    ("Cotton Socks (Pack of 3)", "6115", (99, 249)),
    # Home / personal care
    ("Bathing Soap (Pack of 4)", "3401", (99, 199)),
    ("Shampoo 340ml", "3305", (180, 350)),
    ("Toothpaste 200g", "3306", (85, 150)),
    ("Detergent Powder 1kg", "3402", (110, 190)),
    ("Steel Water Bottle", "7323", (250, 600)),
    ("Plastic Storage Box", "3924", (150, 450)),
]

# --- Restaurant/dhaba catalog (added after a real dhaba bill - "Dhaba
# Punjabi" - was fed through the deployed model and got confidently WRONG
# results: vendor read as "Punjabi Namaste", total as "Brand Total
# EUR1265.6". Root cause traced to training data: every synthetic vendor
# above is retail/kirana-shop themed, and the model had never once seen a
# restaurant name, a food item, or the "Category Name" word order real
# dhaba names often use ("Dhaba Punjabi", not "Punjabi Dhaba's General
# Store"). This is the fix for that gap, not a guess - see results-log.md. ---
RESTAURANT_ITEM_CATALOG = [
    ("Butter Tandoori Roti", "2106", (25, 45)),
    ("Plain Roti", "2106", (10, 20)),
    ("Paneer Lababdar", "2106", (180, 280)),
    ("Paneer Butter Masala", "2106", (180, 290)),
    ("Dal Makhani", "2106", (140, 220)),
    ("Veg Biryani", "1006", (120, 220)),
    ("Chicken Biryani", "1006", (180, 320)),
    ("Masala Dosa", "2106", (60, 110)),
    ("Idli Sambar", "2106", (50, 90)),
    ("Veg Thali", "2106", (120, 220)),
    ("Paneer Tikka", "2106", (200, 320)),
    ("Butter Naan", "2106", (30, 55)),
    ("Chicken Curry", "0207", (220, 350)),
    ("Water Bottle", "2201", (15, 30)),
    ("Cold Drink 250ml", "2202", (30, 50)),
    ("Lassi", "0403", (50, 90)),
    ("Gulab Jamun (2pc)", "1905", (40, 70)),
    ("Parcel Charges", "9963", (5, 20)),
    ("Packing Charges", "9963", (5, 20)),
]

# Real dhaba/restaurant names go either word-order ("Dhaba Punjabi" AND
# "Punjabi Dhaba" both exist) - unlike the retail catalog above, which is
# always "Name + Shop-Type". random_restaurant_vendor_name() randomizes the
# order itself, not just the words, to cover both real patterns.
RESTAURANT_NAME_WORDS = [
    "Punjabi", "Annapurna", "Shanti", "Udupi", "Sagar", "Balaji", "Krishna",
    "Ganesh", "Raj", "Taj", "Deluxe", "Sai", "Maratha", "Andhra",
    "South Indian", "New", "Royal",
]
RESTAURANT_CATEGORY_WORDS = [
    "Dhaba", "Hotel", "Restaurant", "Bhojanalay", "Mess", "Cafe",
    "Family Restaurant", "Fast Food Corner", "Sweets & Restaurant",
]

# Vendor name building blocks (naam + shop-type suffix combos)
VENDOR_PREFIXES = [
    "Sharma", "Gupta", "Patel", "Reddy", "Krishna", "Om Sai", "Shree Ganesh",
    "New Delhi", "Bharat", "Shubham", "Maa Durga", "Sai Ram", "Laxmi",
    "Royal", "City", "Metro", "National", "Anand", "Verma", "Agarwal",
]
VENDOR_SUFFIXES = [
    "General Store", "Traders", "Electronics", "Provision Store",
    "Stationery Mart", "Super Market", "Kirana Store", "Enterprises",
    "Retail Shop", "Departmental Store", "Mobile Shop", "Garments",
]

INDIAN_CITIES = [
    "New Delhi", "Mumbai", "Bengaluru", "Pune", "Hyderabad", "Chennai",
    "Kolkata", "Ahmedabad", "Jaipur", "Lucknow", "Indore", "Nagpur",
]

# State code (first 2 digits of GSTIN) per state - subset of real codes
STATE_GST_CODES = {
    "Delhi": "07", "Maharashtra": "27", "Karnataka": "29", "Tamil Nadu": "33",
    "Gujarat": "24", "West Bengal": "19", "Telangana": "36", "Rajasthan": "08",
    "Uttar Pradesh": "09", "Madhya Pradesh": "23",
}

# GST slabs actually used in India: CGST% + SGST% (equal split of total GST%)
GST_SLABS = [2.5, 6.0, 9.0, 14.0]  # -> 5%, 12%, 18%, 28% combined


def random_gstin(rng):
    """
    Real GSTIN format: 2-digit state code + 10-char PAN-style
    (5 letters + 4 digits + 1 letter) + 1 entity code + 'Z' + 1 checksum.
    Hum sirf VISUALLY-realistic format bana rahe hain (extraction task ke
    liye) - asli checksum algorithm implement nahi kar rahe, wo tax-filing
    ke liye zaroori hota, humare OCR/extraction demo ke liye nahi.
    """
    state_code = rng.choice(list(STATE_GST_CODES.values()))
    letters5 = "".join(rng.choices(string.ascii_uppercase, k=5))
    digits4 = "".join(rng.choices(string.digits, k=4))
    letter1 = rng.choice(string.ascii_uppercase)
    entity = str(rng.randint(1, 9))
    checksum = rng.choice(string.ascii_uppercase + string.digits)
    return f"{state_code}{letters5}{digits4}{letter1}{entity}Z{checksum}"


def random_vendor_name(rng):
    return f"{rng.choice(VENDOR_PREFIXES)} {rng.choice(VENDOR_SUFFIXES)}"


def random_restaurant_vendor_name(rng):
    name = rng.choice(RESTAURANT_NAME_WORDS)
    category = rng.choice(RESTAURANT_CATEGORY_WORDS)
    return f"{category} {name}" if rng.random() < 0.5 else f"{name} {category}"


def random_invoice_no(rng):
    return f"INV-{rng.randint(1000, 9999)}"


def random_date(rng):
    day = rng.randint(1, 28)
    month = rng.randint(1, 12)
    year = rng.choice([2025, 2026])
    return f"{day:02d}/{month:02d}/{year}"


def random_items(rng, n_min=2, n_max=6):
    return rng.sample(ITEM_CATALOG, k=rng.randint(n_min, n_max))


def random_restaurant_items(rng, n_min=2, n_max=6):
    n = min(rng.randint(n_min, n_max), len(RESTAURANT_ITEM_CATALOG))
    return rng.sample(RESTAURANT_ITEM_CATALOG, k=n)


# --- Phase 5.2: more Indian business types (user ne explicitly maanga -
# "restaurant medical agriculture electronic shoes grocery real world jo
# bhi hote hai") - ek hi retail/restaurant se aage badhke asli India ke
# common shop types cover karte hain. Har type ki apni item list + apna
# vendor-naming pattern hai (naming conventions alag-alag hote hain asli
# duniya mein - verified via web search, e.g. agri stores "X Krishi
# Kendra" / "X Krishi Seva Kendra" pattern - real IndiaMART listings match
# this exactly). HSN codes chapter-level realistic hain (pharma=30,
# fertilizer/pesticide=31/38, footwear=64, electronics=85). ---

# Medical / pharmacy
MEDICAL_ITEM_CATALOG = [
    ("Paracetamol 650mg (Strip of 10)", "3004", (15, 35)),
    ("Crocin Advance (Strip of 15)", "3004", (25, 45)),
    ("ORS Powder Sachet", "3004", (15, 25)),
    ("Cough Syrup 100ml", "3004", (60, 120)),
    ("Antiseptic Liquid 100ml", "3004", (45, 90)),
    ("Bandage Roll", "3005", (20, 45)),
    ("Cotton Roll 100g", "3005", (35, 70)),
    ("Digital Thermometer", "9025", (150, 350)),
    ("Vitamin C Tablets (Strip of 15)", "3004", (30, 60)),
    ("Multivitamin Capsules (Strip of 15)", "3004", (60, 150)),
    ("Antacid Tablets (Strip of 10)", "3004", (20, 40)),
    ("Pain Relief Spray", "3004", (120, 220)),
    ("Hand Sanitizer 200ml", "3808", (60, 120)),
    ("Face Mask (Box of 50)", "6307", (150, 300)),
    ("Glucose Powder 200g", "3004", (40, 70)),
    ("B-Complex Tablets (Strip of 15)", "3004", (35, 65)),
    ("Calcium Tablets (Strip of 15)", "3004", (40, 80)),
    ("Eye Drops 10ml", "3004", (45, 95)),
]
MEDICAL_NAME_WORDS = [
    "Sharma", "Gupta", "City", "New Life", "Om Sai", "Shree", "Krishna",
    "National", "Apex", "Wellness", "Care Plus", "Modern", "Ashirwad",
]
MEDICAL_CATEGORY_WORDS = [
    "Medical Store", "Medicos", "Pharmacy", "Chemist", "Medical & General Store",
    "Health Care", "Drug House", "Medical Hall",
]

# Agriculture / krishi kendra
AGRICULTURE_ITEM_CATALOG = [
    ("Urea Fertilizer 45kg Bag", "3102", (250, 350)),
    ("DAP Fertilizer 50kg Bag", "3105", (1200, 1500)),
    ("NPK Fertilizer 50kg Bag", "3105", (1100, 1400)),
    ("Hybrid Maize Seeds 1kg", "1005", (180, 350)),
    ("Hybrid Cotton Seeds 450g", "1207", (700, 950)),
    ("Vegetable Seeds Packet", "1209", (30, 90)),
    ("Pesticide Spray 1L", "3808", (250, 550)),
    ("Insecticide 500ml", "3808", (180, 420)),
    ("Weedicide 1L", "3808", (300, 600)),
    ("Sickle (Hasiya)", "8201", (60, 120)),
    ("Khurpi (Hand Hoe)", "8201", (40, 90)),
    ("Sprayer Pump 16L", "8424", (900, 1600)),
    ("Micronutrient Mixture 1kg", "3105", (150, 300)),
    ("Vermi Compost 50kg Bag", "3101", (280, 420)),
    ("Drip Irrigation Pipe (per meter)", "3917", (8, 18)),
    ("Gumboot Pair", "6401", (250, 450)),
    ("Farmer Gloves (Pair)", "4015", (40, 90)),
]
AGRICULTURE_NAME_WORDS = [
    "Balaji", "Prakash", "Santosh", "Kisan", "Bharat", "Annadata",
    "Jai Kisan", "Shivshakti", "Om", "Maa Bhagwati", "Krishna", "Kirti",
]
AGRICULTURE_CATEGORY_WORDS = [
    "Krishi Kendra", "Krishi Seva Kendra", "Krishi Raksha Kendra",
    "Agro Store", "Beej Bhandar", "Fertilizer & Seeds", "Kisan Seva Kendra",
    "Agro Agencies",
]

# Electronics / appliances (dedicated store - bigger ticket items than
# the small electronics subset already inside the generic ITEM_CATALOG)
ELECTRONICS_ITEM_CATALOG = [
    ("Mobile Phone", "8517", (8000, 25000)),
    ("LED TV 32 Inch", "8528", (12000, 22000)),
    ("Bluetooth Speaker", "8518", (800, 3000)),
    ("Wired Earphones", "8518", (150, 500)),
    ("Mixer Grinder", "8509", (2000, 4500)),
    ("Electric Iron", "8516", (600, 1500)),
    ("Table Fan", "8414", (900, 2000)),
    ("Induction Cooktop", "8516", (1500, 3000)),
    ("Washing Machine (Single Door)", "8450", (10000, 22000)),
    ("Refrigerator (Single Door)", "8418", (11000, 20000)),
    ("Microwave Oven", "8516", (5000, 9000)),
    ("Water Purifier", "8421", (4000, 9000)),
    ("Electric Kettle", "8516", (400, 900)),
    ("Hair Dryer", "8516", (450, 1200)),
    ("Trimmer", "8510", (600, 1800)),
    ("LED Bulb 9W", "8539", (60, 150)),
    ("Extension Board", "8536", (250, 700)),
    ("HDMI Cable", "8544", (150, 500)),
    ("Memory Card 32GB", "8523", (300, 700)),
    ("Power Bank 10000mAh", "8507", (799, 1999)),
]
ELECTRONICS_NAME_WORDS = [
    "City", "Metro", "National", "Modern", "Digital", "Universal",
    "Global", "Smart", "New Era", "Prime", "Shree",
]
ELECTRONICS_CATEGORY_WORDS = [
    "Electronics", "Electricals", "Digital World", "Mobile Point",
    "Home Appliances", "Electronics Hub", "Electronic Centre",
]

# Footwear
FOOTWEAR_ITEM_CATALOG = [
    ("Men's Sports Shoes", "6404", (500, 1500)),
    ("Women's Sandals", "6402", (350, 1200)),
    ("Kids School Shoes", "6404", (300, 700)),
    ("Leather Formal Shoes", "6403", (900, 2500)),
    ("Slippers (Pair)", "6402", (100, 300)),
    ("Sneakers", "6404", (700, 2000)),
    ("Chappal (Pair)", "6402", (80, 250)),
    ("Running Shoes", "6404", (900, 2500)),
    ("Loafers", "6403", (800, 2200)),
    ("Sports Sandals", "6402", (300, 800)),
    ("Shoe Polish", "3405", (30, 70)),
    ("Socks (Pack of 3)", "6115", (99, 249)),
    ("Insole Pair", "6406", (100, 250)),
    ("Shoe Laces", "6406", (20, 50)),
]
FOOTWEAR_NAME_WORDS = [
    "City", "Comfort", "Style", "Royal", "Modern", "Trendy", "Classic",
    "Elite", "New", "Shree",
]
FOOTWEAR_CATEGORY_WORDS = [
    "Footwear", "Shoe Mart", "Shoe Palace", "Foot Care", "Shoe Point",
    "Fashion Footwear", "Footwear Store",
]

# Grocery / kirana (dedicated pure-food catalog - bigger and more focused
# than the mixed general ITEM_CATALOG above, since grocery/kirana is the
# single most common small-shop type in India)
GROCERY_ITEM_CATALOG = [
    ("Basmati Rice 5kg", "1006", (350, 650)),
    ("Wheat Flour (Atta) 5kg", "1101", (180, 280)),
    ("Sugar 1kg", "1701", (40, 60)),
    ("Salt 1kg", "2501", (18, 28)),
    ("Toor Dal 1kg", "0713", (120, 180)),
    ("Moong Dal 1kg", "0713", (110, 170)),
    ("Chana Dal 1kg", "0713", (90, 140)),
    ("Urad Dal 1kg", "0713", (110, 170)),
    ("Sunflower Oil 1L", "1507", (140, 220)),
    ("Mustard Oil 1L", "1514", (150, 230)),
    ("Tea Powder 250g", "0902", (90, 180)),
    ("Coffee Powder 200g", "0901", (110, 220)),
    ("Milk Powder 500g", "0402", (220, 380)),
    ("Besan (Gram Flour) 1kg", "1106", (90, 140)),
    ("Poha 500g", "1904", (35, 60)),
    ("Rava (Semolina) 1kg", "1101", (50, 85)),
    ("Maida 1kg", "1101", (40, 65)),
    ("Jaggery (Gur) 1kg", "1701", (60, 100)),
    ("Turmeric Powder 200g", "0910", (40, 80)),
    ("Red Chilli Powder 200g", "0904", (45, 90)),
    ("Coriander Powder 200g", "0910", (35, 70)),
    ("Garam Masala 100g", "0910", (50, 100)),
    ("Papad (Pack)", "1905", (35, 70)),
    ("Pickle (Achar) 400g", "2001", (70, 140)),
    ("Biscuits Pack", "1905", (20, 60)),
    ("Namkeen Pack 200g", "2106", (40, 90)),
    ("Bathing Soap (Pack of 4)", "3401", (99, 199)),
    ("Detergent Powder 1kg", "3402", (110, 190)),
    ("Matchbox (Pack of 10)", "3605", (10, 20)),
    ("Agarbatti (Incense Sticks)", "3307", (25, 60)),
]
GROCERY_NAME_WORDS = [
    "Sharma", "Gupta", "Patel", "Krishna", "Om Sai", "Shree Ganesh",
    "Maa Durga", "Sai Ram", "Laxmi", "New Delhi", "Bharat", "Anand",
]
GROCERY_CATEGORY_WORDS = [
    "Kirana Store", "General Store", "Provision Store", "Super Market",
    "Grocery Mart", "Departmental Store", "Kirana & General Store",
]


# Apparel / clothing store
APPAREL_ITEM_CATALOG = [
    ("Cotton T-Shirt", "6109", (299, 799)),
    ("Formal Shirt", "6205", (599, 1499)),
    ("Casual Shirt", "6205", (449, 1199)),
    ("Denim Jeans", "6203", (899, 2199)),
    ("Formal Trouser", "6203", (699, 1799)),
    ("Cotton Shorts", "6203", (349, 799)),
    ("Men's Innerwear (Pack of 3)", "6107", (299, 649)),
    ("Women's Innerwear (Pack of 3)", "6108", (299, 649)),
    ("Kurta (Men's)", "6211", (499, 1299)),
    ("Kurti (Women's)", "6211", (399, 1099)),
    ("Saree", "6211", (799, 2999)),
    ("Leggings", "6104", (299, 599)),
    ("Track Pants", "6103", (499, 999)),
    ("Cotton Socks (Pack of 3)", "6115", (99, 249)),
    ("Woolen Sweater", "6110", (699, 1599)),
    ("Jacket", "6201", (999, 2999)),
    ("Kids T-Shirt", "6109", (199, 499)),
    ("School Uniform Set", "6211", (599, 1299)),
]
APPAREL_NAME_WORDS = [
    "City", "Fashion", "New", "Royal", "Trendy", "Style", "Modern",
    "Elite", "Classic", "Shree", "National",
]
APPAREL_CATEGORY_WORDS = [
    "Garments", "Fashion World", "Collection", "Cloth House", "Textiles",
    "Boutique", "Fashion Hub", "Readymade Centre", "Apparels",
]

# Cosmetics / perfumes / beauty
COSMETICS_ITEM_CATALOG = [
    ("Perfume Spray 100ml", "3303", (299, 1499)),
    ("Deodorant Spray 150ml", "3307", (150, 350)),
    ("Face Cream 50g", "3304", (99, 399)),
    ("Face Wash 100ml", "3304", (99, 299)),
    ("Lipstick", "3304", (149, 599)),
    ("Kajal / Eyeliner", "3304", (49, 199)),
    ("Compact Powder", "3304", (99, 349)),
    ("Nail Polish", "3304", (49, 149)),
    ("Talcum Powder 200g", "3304", (79, 179)),
    ("Hair Oil 200ml", "3305", (99, 249)),
    ("Shampoo 340ml", "3305", (180, 350)),
    ("Conditioner 200ml", "3305", (150, 320)),
    ("Body Lotion 200ml", "3304", (129, 349)),
    ("Sunscreen Lotion 100ml", "3304", (199, 499)),
    ("Hair Gel 100ml", "3305", (99, 249)),
    ("Makeup Kit", "3304", (399, 1499)),
    ("Bindi Pack", "3304", (10, 30)),
]
COSMETICS_NAME_WORDS = [
    "City", "New", "Royal", "Shree", "Glamour", "Elite", "Pretty",
    "Sundari", "Modern", "National",
]
COSMETICS_CATEGORY_WORDS = [
    "Cosmetics", "Perfumes", "Beauty World", "Fragrance House",
    "Beauty Parlour Store", "Cosmetic Centre", "Beauty & Cosmetics",
]


def _random_shop_vendor_name(rng, name_words, category_words):
    """Shared 'Name Category' / 'Category Name' randomizer used by every
    non-restaurant business type below - real Indian shop boards go both
    ways ("Sharma Medical Store" and "City Medical Store" both common)."""
    name = rng.choice(name_words)
    category = rng.choice(category_words)
    return f"{name} {category}" if rng.random() < 0.5 else f"{category} {name}"


def random_medical_vendor_name(rng):
    return _random_shop_vendor_name(rng, MEDICAL_NAME_WORDS, MEDICAL_CATEGORY_WORDS)


def random_agriculture_vendor_name(rng):
    return _random_shop_vendor_name(rng, AGRICULTURE_NAME_WORDS, AGRICULTURE_CATEGORY_WORDS)


def random_electronics_vendor_name(rng):
    return _random_shop_vendor_name(rng, ELECTRONICS_NAME_WORDS, ELECTRONICS_CATEGORY_WORDS)


def random_footwear_vendor_name(rng):
    return _random_shop_vendor_name(rng, FOOTWEAR_NAME_WORDS, FOOTWEAR_CATEGORY_WORDS)


def random_grocery_vendor_name(rng):
    return _random_shop_vendor_name(rng, GROCERY_NAME_WORDS, GROCERY_CATEGORY_WORDS)


def random_apparel_vendor_name(rng):
    return _random_shop_vendor_name(rng, APPAREL_NAME_WORDS, APPAREL_CATEGORY_WORDS)


def random_cosmetics_vendor_name(rng):
    return _random_shop_vendor_name(rng, COSMETICS_NAME_WORDS, COSMETICS_CATEGORY_WORDS)


def _random_catalog_items(rng, catalog, n_min=2, n_max=6):
    n = min(rng.randint(n_min, n_max), len(catalog))
    return rng.sample(catalog, k=n)


def random_medical_items(rng, n_min=2, n_max=6):
    return _random_catalog_items(rng, MEDICAL_ITEM_CATALOG, n_min, n_max)


def random_agriculture_items(rng, n_min=2, n_max=6):
    return _random_catalog_items(rng, AGRICULTURE_ITEM_CATALOG, n_min, n_max)


def random_electronics_items(rng, n_min=1, n_max=4):
    # Electronics items are big-ticket - real bills usually have fewer line items
    return _random_catalog_items(rng, ELECTRONICS_ITEM_CATALOG, n_min, n_max)


def random_footwear_items(rng, n_min=2, n_max=6):
    return _random_catalog_items(rng, FOOTWEAR_ITEM_CATALOG, n_min, n_max)


def random_grocery_items(rng, n_min=3, n_max=8):
    return _random_catalog_items(rng, GROCERY_ITEM_CATALOG, n_min, n_max)


def random_apparel_items(rng, n_min=1, n_max=5):
    return _random_catalog_items(rng, APPAREL_ITEM_CATALOG, n_min, n_max)


def random_cosmetics_items(rng, n_min=2, n_max=6):
    return _random_catalog_items(rng, COSMETICS_ITEM_CATALOG, n_min, n_max)
