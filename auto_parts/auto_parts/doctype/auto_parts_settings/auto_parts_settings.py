# Copyright (c) 2026, Masood Javid and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AutoPartsSettings(Document):
	pass

import frappe
from frappe.utils import today

def create_reorder_material_requests():
    config = frappe.get_single("Auto Parts Settings")  # ← "Auto Parts Setup" that
    
    if not config.reorder_warehouse or not config.reorder_level:
        frappe.throw("Reorder Warehouse / Level not set in Auto Parts Settings")

    items = frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0}, fields=["item_code", "item_name"])
    created = []

    for item in items:
        actual_qty = frappe.db.get_value("Bin",
            {"item_code": item.item_code, "warehouse": config.reorder_warehouse}, "actual_qty") or 0

        if actual_qty >= config.reorder_level:
            continue
        
        # Skip if draft MR already exists
        if frappe.db.exists("Material Request Item", {"item_code": item.item_code, "docstatus": 0}):
            continue

        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Purchase"
        mr.transaction_date = mr.schedule_date = today()
        mr.company = frappe.defaults.get_defaults().get("company")
        mr.append("items", {
            "item_code": item.item_code,
            "qty": config.reorder_qty,
            "schedule_date": today(),
            "warehouse": config.reorder_warehouse,
            "uom": frappe.db.get_value("Item", item.item_code, "stock_uom"),
        })
        mr.insert(ignore_permissions=True)
        created.append(item.item_code)

    return {"created": len(created), "items": created}