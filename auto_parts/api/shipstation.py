# auto_parts/integrations/shipstation.py
import frappe
import requests
from base64 import b64encode

class ShipStationConnector:
    BASE_URL = "https://ssapi.shipstation.com"
    # auto_parts/utils/shipping.py

    def get_carrier_credentials(self, carrier):
        settings = frappe.get_single('Auto Parts Settings')
        
        if carrier == 'shipstation':
            return {
                'api_key': settings.shipstation_api_key,
                'api_secret': settings.shipstation_api_secret
            }
        elif carrier == 'ups':
            return {
                'api_key': settings.ups_api_key,
                'account_number': settings.ups_account_number
            }
        elif carrier == 'fedex':
            return {
                'api_key': settings.fedex_api_key,
                'account_number': settings.fedex_account_number
            }
        elif carrier == 'usps':
            return {
                'user_id': settings.usps_user_id
            }

    def __init__(self):
        creds = self.get_carrier_credentials('shipstation')
        token = b64encode(
            f"{creds['api_key']}:{creds['api_secret']}".encode()
        ).decode()
        self.headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }

    def get_rates(self, payload):
        res = requests.post(
            f"{self.BASE_URL}/shipments/getrates",
            json=payload,
            headers=self.headers
        )
        res.raise_for_status()
        return res.json()

    def create_label(self, payload):
        res = requests.post(
            f"{self.BASE_URL}/orders/createlabelfororder",
            json=payload,
            headers=self.headers
        )
        res.raise_for_status()
        return res.json()

    def get_tracking(self, carrier_code, tracking_number):
        res = requests.get(
            f"{self.BASE_URL}/shipments",
            params={
                'trackingNumber': tracking_number,
                'carrierCode': carrier_code
            },
            headers=self.headers
        )
        res.raise_for_status()
        return res.json()