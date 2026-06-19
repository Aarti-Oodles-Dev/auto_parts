#!/usr/bin/env python3
"""
AutoCare DB se ERPNext Doctypes mein Data Migrate karo

Run karne ka tarika (D2 se - frappe-bench folder mein):
  bench --site autos.com execute auto_parts.api.autocare_migration.run_migration

Ya alag alag:
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_makes
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_models
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_base_vehicles
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_part_terminologies
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_brands
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_part_categories
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_part_sub_categories
  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_vehicles
"""

import frappe
import pymysql

# =============================================
# MySQL Config - apna password yahan daal
# =============================================
AUTOCARE_DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",   # <--- apna MySQL root password
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

BATCH_SIZE = 500


def get_conn(db_name):
    config = AUTOCARE_DB_CONFIG.copy()
    config["db"] = db_name
    return pymysql.connect(**config)


def bulk_insert(doctype, rows):
    """ERPNext mein bulk insert"""
    if not rows:
        return 0

    inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        for row in batch:
            try:
                if frappe.db.exists(doctype, row["name"]):
                    continue
                doc = frappe.new_doc(doctype)
                doc.update(row)
                doc.flags.ignore_permissions = True
                doc.flags.ignore_mandatory = True
                doc.insert()
                inserted += 1
            except Exception as e:
                pass  # duplicate ya error skip

        frappe.db.commit()
        print(f"  Inserted so far: {inserted}")

    return inserted


# =============================================
# MIGRATION FUNCTIONS
# =============================================

def migrate_makes():
    """
    autocare_vcdb.Make -> tabVCdb Make
    ERPNext fields: name, make_id, make_name, culture_id, effective_date, end_date
    """
    print("\n=== Migrating: VCdb Makes ===")
    conn = get_conn("autocare_vcdb")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MakeID, MakeName, CultureID, EffectiveDateTime, EndDateTime
        FROM Make
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"MAKE-{r['MakeID']}",
            "make_id": str(r["MakeID"]),
            "make_name": r["MakeName"],
            "culture_id": r.get("CultureID") or "",
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("VCdb Make", rows)
    print(f"  DONE: {count} makes inserted")


def migrate_models():
    """
    autocare_vcdb.Model -> tabVCdb Model
    ERPNext fields: name, model_id, model_name, make_id, vehicle_type_id,
                    culture_id, effective_date, end_date
    """
    print("\n=== Migrating: VCdb Models ===")
    conn = get_conn("autocare_vcdb")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ModelID, ModelName, VehicleTypeID, CultureID, EffectiveDateTime, EndDateTime
        FROM Model
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"MODEL-{r['ModelID']}",
            "model_id": str(r["ModelID"]),
            "model_name": r["ModelName"] or "",
            "vehicle_type_id": str(r["VehicleTypeID"]) if r.get("VehicleTypeID") else "",
            "culture_id": r.get("CultureID") or "",
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("VCdb Model", rows)
    print(f"  DONE: {count} models inserted")


def migrate_base_vehicles():
    """
    autocare_vcdb.BaseVehicle + Make + Model -> tabVCdb Base Vehicle
    ERPNext fields: name, vcdb_id, year, make_id, make, model_id, model,
                    submodel, engine, effective_date, end_date
    Note: submodel aur engine BaseVehicle table mein nahi hote isliye blank rahenge
    """
    print("\n=== Migrating: VCdb Base Vehicles ===")
    conn = get_conn("autocare_vcdb")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            bv.BaseVehicleID,
            bv.YearID,
            bv.MakeID,
            mk.MakeName,
            bv.ModelID,
            mo.ModelName,
            bv.EffectiveDateTime,
            bv.EndDateTime
        FROM BaseVehicle bv
        LEFT JOIN Make mk ON bv.MakeID = mk.MakeID
        LEFT JOIN Model mo ON bv.ModelID = mo.ModelID
        ORDER BY bv.YearID DESC
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"BV-{r['BaseVehicleID']}",
            "vcdb_id": str(r["BaseVehicleID"]),
            "year": r["YearID"],
            "make_id": str(r["MakeID"]),
            "make": r.get("MakeName") or "",
            "model_id": str(r["ModelID"]),
            "model": r.get("ModelName") or "",
            "submodel": "",
            "engine": "",
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("VCdb Base Vehicle", rows)
    print(f"  DONE: {count} base vehicles inserted")


def migrate_part_terminologies():
    """
    autocare_pcdb.Parts -> tabPCdb Part Terminology
    ERPNext fields: name, part_terminology_id, part_terminology_name,
                    part_terminology_description, culture_id, effective_date, end_date
    """
    print("\n=== Migrating: PCdb Part Terminologies ===")
    conn = get_conn("autocare_pcdb")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT PartTerminologyID, PartTerminologyName, PartTerminologyDescription,
               CultureID, EffectiveDateTime, EndDateTime
        FROM Parts
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"PT-{r['PartTerminologyID']}",
            "part_terminology_id": str(r["PartTerminologyID"]),
            "part_terminology_name": r["PartTerminologyName"],
            "part_terminology_description": r.get("PartTerminologyDescription") or "",
            "culture_id": r.get("CultureID") or "",
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("PCdb Part Terminology", rows)
    print(f"  DONE: {count} part terminologies inserted")


def migrate_brands():
    """
    autocare_brands.brand_table -> tabAC Brand
    ERPNext fields: name, brand_id, brand_name, parent_id, parent_company,
                    sub_brand_id, sub_brand_name, is_oem, effective_date, end_date
    """
    print("\n=== Migrating: AC Brands ===")
    conn = get_conn("autocare_brands")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT RecordID, BrandID, BrandName, ParentID, ParentCompany,
               SubBrandID, SubBrandName, BrandOEMFlag, EffectiveDateTime, EndDateTime
        FROM brand_table
        WHERE EndDateTime IS NULL
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"BRAND-{r['RecordID']}",
            "brand_id": str(r["BrandID"]),
            "brand_name": r["BrandName"],
            "parent_id": r.get("ParentID") or "",
            "parent_company": r.get("ParentCompany") or "",
            "sub_brand_id": r.get("SubBrandID") or "",
            "sub_brand_name": r.get("SubBrandName") or "",
            "is_oem": 1 if r.get("BrandOEMFlag") else 0,
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("AC Brand", rows)
    print(f"  DONE: {count} brands inserted")


def migrate_part_categories():
    """
    autocare_pcdb.Categories -> tabAC Part Category
    ERPNext fields: name, category_id, category_name, effective_date, end_date
    """
    print("\n=== Migrating: AC Part Categories ===")
    conn = get_conn("autocare_pcdb")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CategoryID, CategoryName, EffectiveDateTime, EndDateTime
        FROM Categories
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"CAT-{r['CategoryID']}",
            "category_id": str(r["CategoryID"]),
            "category_name": r["CategoryName"],
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("AC Part Category", rows)
    print(f"  DONE: {count} categories inserted")


def migrate_part_sub_categories():
    """
    autocare_pcdb.SubCategories -> tabAC Part Sub Category
    ERPNext fields: name, sub_category_id, sub_category_name, effective_date, end_date
    """
    print("\n=== Migrating: AC Part Sub Categories ===")
    conn = get_conn("autocare_pcdb")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT SubCategoryID, SubCategoryName, EffectiveDateTime, EndDateTime
        FROM SubCategories
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"SUBCAT-{r['SubCategoryID']}",
            "sub_category_id": str(r["SubCategoryID"]),
            "sub_category_name": r["SubCategoryName"],
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("AC Part Sub Category", rows)
    print(f"  DONE: {count} sub categories inserted")


def migrate_vehicles():
    """
    autocare_vcdb.Vehicle + joins -> tabAC Vehicle (custom doctype)
    ERPNext fields: name, vcdb_vehicle_id, vcdb_base_vehicle_id, year,
                    make, model, submodel, region, publication_stage,
                    effective_date, end_date
    NOTE: Bahut bada dataset (~7 lakh rows)
          Pehle 2023+ se test karo, WHERE clause hata do sab ke liye
    """
    print("\n=== Migrating: AC Vehicles (2023+) ===")
    conn = get_conn("autocare_vcdb")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            v.VehicleID,
            v.BaseVehicleID,
            bv.YearID,
            mk.MakeName,
            mo.ModelName,
            sm.SubModelName,
            r.RegionName,
            ps.PublicationStageName,
            v.EffectiveDateTime,
            v.EndDateTime
        FROM Vehicle v
        JOIN BaseVehicle bv ON v.BaseVehicleID = bv.BaseVehicleID
        LEFT JOIN Make mk ON bv.MakeID = mk.MakeID
        LEFT JOIN Model mo ON bv.ModelID = mo.ModelID
        LEFT JOIN SubModel sm ON v.SubModelID = sm.SubModelID
        LEFT JOIN Region r ON v.RegionID = r.RegionID
        LEFT JOIN PublicationStage ps ON v.PublicationStageID = ps.PublicationStageID
        WHERE bv.YearID >= 2023
        ORDER BY bv.YearID DESC
    """)

    rows = []
    for r in cursor.fetchall():
        rows.append({
            "name": f"VEH-{r['VehicleID']}",
            "vcdb_vehicle_id": str(r["VehicleID"]),
            "vcdb_base_vehicle_id": str(r["BaseVehicleID"]),
            "year": r["YearID"],
            "make": r.get("MakeName") or "",
            "model": r.get("ModelName") or "",
            "submodel": r.get("SubModelName") or "",
            "region": r.get("RegionName") or "",
            "publication_stage": r.get("PublicationStageName") or "",
            "effective_date": r.get("EffectiveDateTime"),
            "end_date": r.get("EndDateTime"),
        })
    conn.close()

    count = bulk_insert("AC Vehicle", rows)
    print(f"  DONE: {count} vehicles inserted (2023+ only)")
    print("  Sab years ke liye WHERE clause hata do aur migrate_vehicles dobara chalao")


def run_migration():
    """
    Sab kuch ek saath chalao
    Vehicles alag chalao kyunki wo bahut bada dataset hai
    """
    print("=" * 50)
    print("AutoCare -> ERPNext Full Migration Start")
    print("=" * 50)

    migrate_makes()
    migrate_models()
    migrate_base_vehicles()
    migrate_part_terminologies()
    migrate_brands()
    migrate_part_categories()
    migrate_part_sub_categories()
    migrate_vehicles()

    # Vehicles alag chalao - bahut bada dataset hai
    # bench --site autos.com execute auto_parts.api.autocare_migration.migrate_vehicles

    print("\n" + "=" * 50)
    print("Migration Complete!")
    print("Vehicles ke liye alag run karo:")
    print("  bench --site autos.com execute auto_parts.api.autocare_migration.migrate_vehicles")
    print("=" * 50)