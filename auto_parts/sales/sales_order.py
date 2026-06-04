# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _
from frappe.utils import flt


def validate_vehicle_garage(doc):
	if not doc.get("vehicle_garage"):
		return

	garage_customer = frappe.db.get_value("Vehicle Garage", doc.vehicle_garage, "customer")
	if garage_customer and garage_customer != doc.customer:
		frappe.throw(
			_("Vehicle Garage {0} belongs to customer {1}, not {2}.").format(
				doc.vehicle_garage, garage_customer, doc.customer
			)
		)


def validate_sales_order(doc, method=None):
	if doc.is_special_order and doc.is_buyout:
		frappe.throw(_("A Sales Order cannot be both Special Order and Buyout."))

	if doc.is_buyout:
		allow_buyout = frappe.db.get_value("Customer", doc.customer, "allow_buyout")
		if not allow_buyout:
			frappe.throw(_("Customer {0} is not allowed for Buyout orders.").format(doc.customer))

	validate_vehicle_garage(doc)


def validate_sales_invoice_garage(doc, method=None):
	copy_vehicle_from_sales_order(doc)
	validate_vehicle_garage(doc)


def _resolve_sales_orders_from_invoice(doc) -> set[str]:
	"""Find linked Sales Order(s) from SI items (SO direct or via Delivery Note)."""
	so_names: set[str] = set()

	for row in doc.get("items", []):
		if row.get("sales_order"):
			so_names.add(row.sales_order)
			continue

		if row.get("dn_detail"):
			so = frappe.db.get_value("Delivery Note Item", row.dn_detail, "against_sales_order")
			if so:
				so_names.add(so)

	for row in doc.get("items", []):
		if not row.get("delivery_note"):
			continue
		dn_items = frappe.get_all(
			"Delivery Note Item",
			filters={
				"parent": row.delivery_note,
				"against_sales_order": ["is", "set"],
			},
			pluck="against_sales_order",
			distinct=True,
		)
		so_names.update(dn_items)

	return so_names


def copy_vehicle_from_sales_order(doc, method=None):
	if doc.get("vehicle_garage"):
		return

	so_names = _resolve_sales_orders_from_invoice(doc)
	if not so_names:
		return

	so_name = next(iter(so_names))
	so_vehicle = frappe.db.get_value(
		"Sales Order", so_name, ["vehicle_garage", "vin"], as_dict=True
	)
	if so_vehicle and so_vehicle.vehicle_garage:
		doc.vehicle_garage = so_vehicle.vehicle_garage
		doc.vin = so_vehicle.vin or ""


@frappe.whitelist()
def get_vehicle_from_sales_order(sales_order: str) -> dict:
	"""Used by Sales Invoice form to pull garage/VIN when created from SO or DN."""
	if not sales_order:
		return {}
	return (
		frappe.db.get_value(
			"Sales Order", sales_order, ["vehicle_garage", "vin"], as_dict=True
		)
		or {}
	)


def on_submit_sales_order(doc, method=None):
	if doc.is_special_order and not _has_linked_po(doc.name, special=True):
		frappe.throw(
			_("Special Order requires a linked Purchase Order. Use Create Special Order PO.")
		)

	if doc.is_buyout and not _has_linked_po(doc.name, buyout=True):
		frappe.throw(_("Buyout order requires a linked Buyout Purchase Order. Use Create Buyout PO."))


def _has_linked_po(sales_order: str, special: bool = False, buyout: bool = False) -> bool:
	filters = {"linked_sales_order": sales_order, "docstatus": ["<", 2]}
	if buyout:
		filters["is_buyout_po"] = 1
	elif special:
		filters["is_buyout_po"] = 0
	return bool(frappe.db.exists("Purchase Order", filters))


@frappe.whitelist()
def get_customer_commercial_details(customer: str) -> dict:
	from auto_parts.sales.customer import get_customer_commercial_details as _get

	return _get(customer)


@frappe.whitelist()
def create_special_order_po(sales_order: str, supplier: str | None = None) -> dict:
	so = frappe.get_doc("Sales Order", sales_order)
	if not so.is_special_order:
		frappe.throw(_("Enable Is Special Order on this Sales Order first."))
	if _has_linked_po(so.name, special=True):
		frappe.throw(_("A Special Order Purchase Order is already linked to this Sales Order."))

	po_name = _create_linked_po(so, supplier=supplier, is_buyout_po=0)
	return {"purchase_order": po_name}


@frappe.whitelist()
def create_buyout_po(sales_order: str, supplier: str | None = None) -> dict:
	so = frappe.get_doc("Sales Order", sales_order)
	if not so.is_buyout:
		frappe.throw(_("Enable Is Buyout on this Sales Order first."))

	allow_buyout = frappe.db.get_value("Customer", so.customer, "allow_buyout")
	if not allow_buyout:
		frappe.throw(_("Customer is not allowed for Buyout orders."))

	if _has_linked_po(so.name, buyout=True):
		frappe.throw(_("A Buyout Purchase Order is already linked to this Sales Order."))

	po_name = _create_linked_po(so, supplier=supplier, is_buyout_po=1)
	return {"purchase_order": po_name}


def _create_linked_po(so, supplier: str | None = None, is_buyout_po: int = 0) -> str:
	if not supplier:
		supplier = _get_default_supplier(so)
	if not supplier:
		frappe.throw(_("Supplier is required to create a Purchase Order."))

	if not so.items:
		frappe.throw(_("Add at least one item to the Sales Order before creating a Purchase Order."))

	po = frappe.new_doc("Purchase Order")
	po.supplier = supplier
	po.company = so.company
	po.currency = frappe.db.get_value("Supplier", supplier, "default_currency") or so.currency
	po.transaction_date = so.transaction_date
	po.schedule_date = so.delivery_date or so.transaction_date
	po.linked_sales_order = so.name
	po.is_buyout_po = is_buyout_po

	for row in so.items:
		po.append(
			"items",
			{
				"item_code": row.item_code,
				"item_name": row.item_name,
				"description": row.description,
				"qty": flt(row.qty),
				"uom": row.uom,
				"stock_uom": row.stock_uom,
				"conversion_factor": row.conversion_factor or 1,
				"rate": flt(row.rate),
				"sales_order": so.name,
				"sales_order_item": row.name,
				"schedule_date": row.delivery_date or so.delivery_date or so.transaction_date,
			},
		)

	po.insert(ignore_permissions=True)
	frappe.msgprint(_("Purchase Order {0} created").format(po.name), indicator="green")
	return po.name


def _get_default_supplier(so) -> str | None:
	for row in so.items:
		item_supplier = frappe.db.get_value("Item Default", {"parent": row.item_code}, "default_supplier")
		if item_supplier:
			return item_supplier

	return frappe.db.get_value(
		"Supplier",
		{"disabled": 0},
		"name",
		order_by="modified desc",
	)
