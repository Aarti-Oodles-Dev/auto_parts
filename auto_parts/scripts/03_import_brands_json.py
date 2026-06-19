#!/usr/bin/env python3
# ============================================================
# STEP 3: AutoCare BrandTable JSON import karo
# D1 se run karo:
#   cd ~/Desktop/Asian-Autos/frappe-bench/apps/auto_parts
#   ~/Desktop/Asian-Autos/frappe-bench/env/bin/python3 auto_parts/scripts/03_import_brands_json.py /home/aarti-kumari/Downloads/AutoCare_BrandTable_V2.json
# ============================================================

import json
import sys
import pymysql

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",   # <--- apna MySQL root password daal
    "db": "autocare_brands",
    "charset": "utf8mb4",
}

def import_brands(json_file):
    print(f"=== Brands JSON import: {json_file} ===")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # BrandTable array dhundo
    brands = []
    if isinstance(data, list):
        brands = data
    elif "BrandTable" in data:
        brands = data["BrandTable"]
    elif "Brand" in data:
        brands = data["Brand"]
    else:
        # Pehli key try karo
        first_key = list(data.keys())[0]
        brands = data[first_key]

    print(f"  Total brands found: {len(brands)}")

    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Table create karo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brand_table (
            RecordID     INT AUTO_INCREMENT PRIMARY KEY,
            ParentID     VARCHAR(10),
            ParentCompany VARCHAR(255),
            BrandID      VARCHAR(10) NOT NULL,
            BrandName    VARCHAR(255) NOT NULL,
            SubBrandID   VARCHAR(10),
            SubBrandName VARCHAR(255),
            BrandOEMFlag TINYINT(1) DEFAULT 0,
            EffectiveDateTime DATETIME,
            EndDateTime  DATETIME,
            INDEX idx_brand_id (BrandID),
            INDEX idx_brand_name (BrandName),
            INDEX idx_parent_id (ParentID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    inserted = 0
    for b in brands:
        try:
            cursor.execute("""
                INSERT IGNORE INTO brand_table
                (ParentID, ParentCompany, BrandID, BrandName, SubBrandID, SubBrandName,
                 BrandOEMFlag, EffectiveDateTime, EndDateTime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                b.get("ParentID") or b.get("parentId"),
                b.get("ParentCompany") or b.get("parentCompany"),
                b.get("BrandID") or b.get("brandId"),
                b.get("BrandName") or b.get("brandName", ""),
                b.get("SubBrandID") or b.get("subBrandId"),
                b.get("SubBrandName") or b.get("subBrandName"),
                1 if b.get("BrandOEMFlag") or b.get("brandOEMFlag") else 0,
                b.get("EffectiveDateTime") or b.get("effectiveDateTime"),
                b.get("EndDateTime") or b.get("endDateTime"),
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e} | Brand: {b.get('BrandName','?')}")

    conn.commit()
    conn.close()
    print(f"  DONE: {inserted} brands imported!")

if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else "/home/aarti-kumari/Downloads/AutoCare_BrandTable_V2.json"
    import_brands(json_file)
    print("Ab Step 4 run karo - bench migrate")