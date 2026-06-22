# auto_parts/api/shipping.py
import frappe
from frappe.utils import flt
from auto_parts.api.shipstation import ShipStationConnector
@frappe.whitelist()
def get_shipping_rates(delivery_note):
    dn = frappe.get_doc('Delivery Note', delivery_note)
    ss = ShipStationConnector()

    payload = {
        "carrierCode": "ups",  # default, user change kar sakta hai
        "fromPostalCode": frappe.db.get_single_value(
            'Auto Parts Settings', 'warehouse_zip'
        ),
        "toState":     dn.shipping_address_name,
        "toPostalCode": dn.custom_ship_to_zip,
        "toCountry":   dn.custom_ship_to_country or "US",
        "weight": {
            "value": sum(
                flt(i.custom_weight) * flt(i.qty)
                for i in dn.items
            ),
            "units": "pounds"
        },
        "dimensions": {
            "units": "inches",
            "length": 12,
            "width":  12,
            "height": 12
        }
    }

    rates = ss.get_rates(payload)
    return rates


@frappe.whitelist()
def create_shipping_label(delivery_note, carrier_code, service_code):
    dn = frappe.get_doc('Delivery Note', delivery_note)
    ss = ShipStationConnector()

    payload = {
        "orderId":     dn.custom_shipstation_order_id,
        "carrierCode": carrier_code,
        "serviceCode": service_code,
        "confirmation": "delivery",
        "testLabel":    False
    }

    result = ss.create_label(payload)

    # Save label URL + tracking back to DN
    dn.db_set('custom_tracking_number', result.get('trackingNumber'))
    dn.db_set('custom_label_url',       result.get('labelData'))
    dn.db_set('custom_carrier',         carrier_code)

    return result
