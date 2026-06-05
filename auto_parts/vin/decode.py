# Copyright (c) 2026, Masood Javid and contributors

import json

import frappe
import requests
from frappe import _
from frappe.utils import cint, now_datetime

DEFAULT_NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"


def normalize_vin(vin: str) -> str:
	return (vin or "").strip().upper()


def validate_vin(vin: str) -> None:
	if len(vin) != 17:
		frappe.throw(_("VIN must be exactly 17 characters."))
	if any(ch in vin for ch in ("I", "O", "Q")):
		frappe.throw(_("VIN cannot contain the letters I, O, or Q."))


def _get_settings():
	return frappe.get_single("Auto Parts Settings")


def _build_api_url(vin: str, settings) -> str:
	if settings.vin_decode_api_url:
		url = settings.vin_decode_api_url.strip()
		if "{vin}" in url:
			return url.format(vin=vin)
		return url.rstrip("/") + "/" + vin
	return DEFAULT_NHTSA_URL.format(vin=vin)


def _fetch_payload(vin: str, settings) -> dict:
	url = _build_api_url(vin, settings)
	headers = {}
	api_key = settings.get_password("vin_decode_api_key") if settings.vin_decode_api_key else None
	if api_key:
		headers["Authorization"] = f"Bearer {api_key}"

	try:
		response = requests.get(url, headers=headers, timeout=30)
		response.raise_for_status()
		return response.json()
	except requests.RequestException as exc:
		frappe.throw(_("VIN decode API request failed: {0}").format(str(exc)))


def _parse_nhtsa(payload: dict) -> dict:
	results = {
		row.get("Variable"): row.get("Value")
		for row in payload.get("Results", [])
		if row.get("Variable")
	}
	year = cint(results.get("Model Year")) or None
	make = (results.get("Make") or "").strip() or None
	model = (results.get("Model") or "").strip() or None
	engine = (results.get("Engine Model") or results.get("DisplacementL") or "").strip() or None

	return {
		"year": year,
		"make": make,
		"model": model,
		"engine": engine,
	}


def _ensure_dict(payload) -> dict:
	if isinstance(payload, dict):
		return payload
	if isinstance(payload, str):
		try:
			return json.loads(payload)
		except json.JSONDecodeError:
			return {}
	return {}


def _parse_payload(payload) -> dict:
	payload = _ensure_dict(payload)
	if "Results" in payload:
		return _parse_nhtsa(payload)

	data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
	if not isinstance(data, dict):
		frappe.throw(_("Unexpected VIN decode API response format."))

	return {
		"year": cint(data.get("year") or data.get("model_year")) or None,
		"make": (data.get("make") or "").strip() or None,
		"model": (data.get("model") or "").strip() or None,
		"engine": (data.get("engine") or "").strip() or None,
	}


def _get_or_create_vehicle_configuration(decoded: dict) -> str | None:
	year, make, model = decoded.get("year"), decoded.get("make"), decoded.get("model")
	if not (year and make and model):
		return None

	existing = frappe.db.get_value(
		"Vehicle Configuration",
		{"year": year, "make": make, "model": model},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Vehicle Configuration",
			"year": year,
			"make": make,
			"model": model,
			"engine": decoded.get("engine"),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _save_cache(vin: str, payload: dict, vehicle_configuration: str | None) -> None:
	if frappe.db.exists("VIN Decode Cache", vin):
		doc = frappe.get_doc("VIN Decode Cache", vin)
	else:
		doc = frappe.new_doc("VIN Decode Cache")
		doc.vin = vin

	doc.decoded_on = now_datetime()
	doc.decode_payload = payload if isinstance(payload, dict) else json.loads(payload)
	doc.vehicle_configuration = vehicle_configuration
	doc.save(ignore_permissions=True)


def _format_response(vin: str, decoded: dict, vehicle_configuration: str | None, from_cache: bool = False) -> dict:
	return {
		"vin": vin,
		"year": decoded.get("year"),
		"make": decoded.get("make"),
		"model": decoded.get("model"),
		"engine": decoded.get("engine"),
		"vehicle_configuration": vehicle_configuration,
		"from_cache": from_cache,
	}


@frappe.whitelist()
def decode_vin(vin: str) -> dict:
	"""Decode VIN via configured API (or NHTSA fallback) and cache the result."""
	vin = normalize_vin(vin)
	validate_vin(vin)
	settings = _get_settings()

	if settings.enable_vin_decode_cache and frappe.db.exists("VIN Decode Cache", vin):
		cached = frappe.get_doc("VIN Decode Cache", vin)
		decoded = {}
		if cached.vehicle_configuration:
			decoded = (
				frappe.db.get_value(
					"Vehicle Configuration",
					cached.vehicle_configuration,
					["year", "make", "model", "engine"],
					as_dict=True,
				)
				or {}
			)
		if not decoded.get("make") and cached.decode_payload:
			decoded = _parse_payload(cached.decode_payload)
		return _format_response(vin, decoded, cached.vehicle_configuration, from_cache=True)

	payload = _fetch_payload(vin, settings)
	decoded = _parse_payload(payload)
	vehicle_configuration = _get_or_create_vehicle_configuration(decoded)

	if settings.enable_vin_decode_cache:
		_save_cache(vin, payload, vehicle_configuration)

	return _format_response(vin, decoded, vehicle_configuration, from_cache=False)


@frappe.whitelist()
def apply_vin_to_sales_order(vin: str, customer: str) -> dict:
	"""Row 91: decode VIN and link matching Vehicle Garage for the customer."""
	if not customer:
		frappe.throw(_("Select a Customer first."))

	result = decode_vin(vin)
	garage = frappe.db.get_value(
		"Vehicle Garage",
		{"vin": result["vin"], "customer": customer, "is_active": 1},
		"name",
	)

	return {
		**result,
		"vehicle_garage": garage,
	}
