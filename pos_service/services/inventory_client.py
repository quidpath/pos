"""Client for calling the Inventory service from POS/Purchases."""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class InventoryClient:
    def __init__(self):
        self.base_url = settings.INVENTORY_SERVICE_URL
        self.secret = settings.INVENTORY_SERVICE_SECRET

    def _headers(self):
        return {"X-Service-Key": self.secret, "Content-Type": "application/json"}

    def create_stock_move(self, payload: dict) -> dict | None:
        try:
            resp = requests.post(
                f"{self.base_url}/api/inventory/stock/moves/",
                json=payload,
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Inventory stock move failed: %s", e)
            return None

    def validate_stock_move(self, move_id: str) -> dict | None:
        try:
            resp = requests.post(
                f"{self.base_url}/api/inventory/stock/moves/{move_id}/validate/",
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Inventory validate move failed: %s", e)
            return None

    def get_stock_level(self, product_id: str, corporate_id: str) -> dict | None:
        try:
            resp = requests.get(
                f"{self.base_url}/api/inventory/stock/summary/{product_id}/",
                headers=self._headers(),
                params={"corporate_id": corporate_id},
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning("Could not get stock level: %s", e)
        return None
