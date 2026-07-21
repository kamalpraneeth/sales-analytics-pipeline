"""
generate_dataset.py — Generate a realistic Superstore-equivalent dataset
=========================================================================
A procedurally generated synthetic retail sales dataset (~9,600 orders), 
modeled on the structure of the public Superstore dataset, used to 
demonstrate the full ETL -> SQL -> BI pipeline.

Dataset structure mirrors the Tableau Superstore Sales dataset:
  - Row ID, Order ID, Order Date, Ship Date, Ship Mode
  - Customer ID, Customer Name, Segment
  - Country, City, State, Postal Code, Region
  - Product ID, Category, Sub-Category, Product Name
  - Sales, Quantity, Discount, Profit

After generation, the file is saved to data/raw/superstore_raw.csv
and the project's cleaning + ETL pipeline can run normally.
"""

import os
import random
import csv
from datetime import date, timedelta

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "superstore_raw.csv")

# ─── Seed for reproducibility ─────────────────────────────────────────────────
random.seed(42)

# ─── Reference tables (match Superstore structure) ────────────────────────────
REGIONS = {
    "West":    ["California", "Washington", "Oregon", "Nevada", "Arizona", "Utah",
                "Colorado", "New Mexico", "Montana", "Idaho", "Wyoming"],
    "East":    ["New York", "Pennsylvania", "Virginia", "North Carolina", "Georgia",
                "Florida", "New Jersey", "Massachusetts", "Connecticut", "Maryland",
                "Delaware", "Rhode Island", "Vermont", "New Hampshire", "Maine"],
    "Central": ["Texas", "Illinois", "Ohio", "Michigan", "Minnesota", "Missouri",
                "Wisconsin", "Indiana", "Iowa", "Nebraska", "Kansas", "Oklahoma",
                "South Dakota", "North Dakota"],
    "South":   ["Alabama", "Mississippi", "Tennessee", "Kentucky", "Arkansas",
                "Louisiana", "West Virginia", "South Carolina"],
}

CITY_BY_STATE = {
    "California": ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento"],
    "New York": ["New York City", "Buffalo", "Rochester", "Syracuse"],
    "Texas": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
    "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville"],
    "Washington": ["Seattle", "Spokane", "Tacoma"],
    "Illinois": ["Chicago", "Springfield", "Rockford"],
    "Pennsylvania": ["Philadelphia", "Pittsburgh", "Allentown"],
    "Ohio": ["Columbus", "Cleveland", "Cincinnati"],
    "Georgia": ["Atlanta", "Savannah", "Augusta"],
    "Virginia": ["Richmond", "Norfolk", "Virginia Beach"],
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_WEIGHTS = [0.52, 0.30, 0.18]

SHIP_MODES = ["Standard Class", "Second Class", "First Class", "Same Day"]
SHIP_WEIGHTS = [0.60, 0.20, 0.15, 0.05]
SHIP_DAYS = {"Standard Class": (5, 7), "Second Class": (3, 5),
             "First Class": (1, 3), "Same Day": (0, 1)}

CATEGORIES = {
    "Furniture": {
        "Chairs":     ("FUR-CH", 40, 300, 0.05, 0.22),
        "Tables":     ("FUR-TA", 70, 500, 0.15, -0.08),   # often loss-making
        "Bookcases":  ("FUR-BO", 40, 300, 0.12, 0.03),
        "Furnishings":("FUR-FU", 5, 50, 0.05, 0.18),
    },
    "Office Supplies": {
        "Binders":    ("OFF-BI", 2, 20, 0.02, 0.32),
        "Paper":      ("OFF-PA", 3, 30, 0.01, 0.40),
        "Storage":    ("OFF-ST", 10, 80, 0.05, 0.20),
        "Art":        ("OFF-AR", 1, 15, 0.01, 0.35),
        "Appliances": ("OFF-AP", 20, 150, 0.08, 0.15),
        "Labels":     ("OFF-LA", 2, 15, 0.01, 0.42),
        "Fasteners":  ("OFF-FA", 1, 8, 0.01, 0.30),
        "Envelopes":  ("OFF-EN", 2, 10, 0.01, 0.38),
        "Supplies":   ("OFF-SU", 5, 40, 0.03, 0.10),
    },
    "Technology": {
        "Phones":     ("TEC-PH", 30, 400, 0.05, 0.17),
        "Accessories":("TEC-AC", 10, 100, 0.04, 0.20),
        "Machines":   ("TEC-MA", 100, 800, 0.10, 0.14),
        "Copiers":    ("TEC-CO", 150, 1200, 0.05, 0.37),
    },
}

PRODUCTS = {}
for cat, subcats in CATEGORIES.items():
    for subcat, (prefix, min_p, max_p, disc_sd, margin) in subcats.items():
        for i in range(1, 6):
            pid = f"{prefix}-{10000 + i * 37}"
            name = f"{subcat} Product {i}"
            PRODUCTS[pid] = {
                "category": cat, "sub_category": subcat,
                "product_name": name,
                "min_price": min_p, "max_price": max_p,
                "discount_sd": disc_sd, "base_margin": margin,
            }

PRODUCT_IDS = list(PRODUCTS.keys())

# ─── Customer pool ─────────────────────────────────────────────────────────────
FIRST_NAMES = ["Aaron", "Adam", "Alan", "Alex", "Alice", "Amanda", "Amy", "Andrew",
               "Angela", "Anna", "Anthony", "Ashley", "Barbara", "Benjamin", "Beth",
               "Brian", "Carol", "Charles", "Chris", "Christina", "Claire", "Daniel",
               "David", "Diana", "Donald", "Donna", "Dorothy", "Douglas", "Edward",
               "Elizabeth", "Emily", "Eric", "Frank", "Gary", "George", "Grace",
               "Hannah", "Harry", "Helen", "Henry", "Jack", "James", "Janet", "Jason",
               "Jennifer", "Jessica", "John", "Joseph", "Julia", "Justin", "Karen",
               "Katherine", "Kelly", "Kenneth", "Kevin", "Kim", "Laura", "Lauren",
               "Linda", "Lisa", "Lori", "Mark", "Mary", "Matthew", "Michael",
               "Michelle", "Nancy", "Nicole", "Patrick", "Paul", "Rachel", "Rebecca",
               "Richard", "Robert", "Ryan", "Sandra", "Sara", "Sarah", "Scott",
               "Shannon", "Sharon", "Stephanie", "Stephen", "Steven", "Susan",
               "Thomas", "Timothy", "Todd", "Tracy", "William"]
LAST_NAMES  = ["Adams", "Allen", "Anderson", "Baker", "Brown", "Campbell", "Carter",
               "Clark", "Collins", "Cook", "Cooper", "Cox", "Davis", "Edwards",
               "Evans", "Fisher", "Foster", "Garcia", "Gonzalez", "Green", "Hall",
               "Harris", "Hernandez", "Hill", "Jackson", "Johnson", "Jones", "Kelly",
               "King", "Lee", "Lewis", "Martin", "Martinez", "Miller", "Mitchell",
               "Moore", "Morgan", "Morris", "Murphy", "Nelson", "Parker", "Peterson",
               "Phillips", "Richardson", "Roberts", "Robinson", "Rodriguez", "Scott",
               "Smith", "Stewart", "Sullivan", "Taylor", "Thomas", "Thompson",
               "Torres", "Turner", "Walker", "White", "Williams", "Wilson", "Wright",
               "Young"]

def make_customers(n=793):
    """Generate a pool of n customers (matches Superstore's ~793 unique customers)."""
    customers = {}
    for _ in range(n):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        seg  = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        cid  = f"CG-{random.randint(10000, 99999)}"
        customers[cid] = {"name": name, "segment": seg}
    return customers

CUSTOMERS = make_customers(793)
CUSTOMER_IDS = list(CUSTOMERS.keys())

# ─── Generation ───────────────────────────────────────────────────────────────
def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_rows(n_orders: int = 5009) -> list:
    """
    Generate n_orders orders (each order may have 1-5 line items).
    Total rows target: ~9,994 (matching original Superstore).
    """
    rows = []
    row_id = 1
    start_date = date(2019, 1, 1)
    end_date   = date(2022, 12, 31)

    for order_num in range(1, n_orders + 1):
        # Order-level fields
        order_id   = f"US-{2019 + (order_num % 4)}-{100000 + order_num}"
        order_date = random_date(start_date, end_date)
        ship_mode  = random.choices(SHIP_MODES, weights=SHIP_WEIGHTS)[0]
        min_days, max_days = SHIP_DAYS[ship_mode]
        ship_date  = order_date + timedelta(days=random.randint(min_days, max_days))

        cid        = random.choice(CUSTOMER_IDS)
        customer   = CUSTOMERS[cid]
        region     = random.choice(list(REGIONS.keys()))
        state      = random.choice(REGIONS[region])
        city       = random.choice(CITY_BY_STATE.get(state, [f"{state} City"]))
        postal     = str(random.randint(10000, 99999))

        n_items = random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.30, 0.15, 0.07, 0.03])[0]
        chosen_products = random.sample(PRODUCT_IDS, min(n_items, len(PRODUCT_IDS)))

        for pid in chosen_products:
            p       = PRODUCTS[pid]
            qty     = random.randint(1, 14)
            price   = round(random.uniform(p["min_price"], p["max_price"]), 2)
            sales   = round(price * qty, 2)

            # Discount: clipped to [0, 0.8]
            disc_raw = random.gauss(0.10, p["discount_sd"])
            discount = round(max(0.0, min(0.8, disc_raw)), 2)

            # Profit: base margin ± noise, penalised by discount
            margin_noise = random.gauss(p["base_margin"], 0.08)
            effective_margin = margin_noise - discount * 0.7
            profit = round(sales * effective_margin, 2)

            rows.append({
                "Row ID":       row_id,
                "Order ID":     order_id,
                "Order Date":   order_date.strftime("%m/%d/%Y"),
                "Ship Date":    ship_date.strftime("%m/%d/%Y"),
                "Ship Mode":    ship_mode,
                "Customer ID":  cid,
                "Customer Name": customer["name"],
                "Segment":      customer["segment"],
                "Country":      "United States",
                "City":         city,
                "State":        state,
                "Postal Code":  postal,
                "Region":       region,
                "Product ID":   pid,
                "Category":     p["category"],
                "Sub-Category": p["sub_category"],
                "Product Name": p["product_name"],
                "Sales":        sales,
                "Quantity":     qty,
                "Discount":     discount,
                "Profit":       profit,
            })
            row_id += 1

    return rows

COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Customer Name", "Segment",
    "Country", "City", "State", "Postal Code", "Region",
    "Product ID", "Category", "Sub-Category", "Product Name",
    "Sales", "Quantity", "Discount", "Profit",
]

def main():
    print("[GEN] Generating Superstore-equivalent dataset (~9,994 rows)...")
    rows = generate_rows(n_orders=5009)
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    with open(RAW_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Saved {len(rows):,} rows -> {RAW_PATH}")
    print(f"     Columns: {COLUMNS}")

if __name__ == "__main__":
    main()
