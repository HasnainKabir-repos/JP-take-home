from typing import Any
import requests
from app.config import Config

class AccountingAPIError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str | None,
        message: str,
        details: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

class AccountingClient:
    def __init__(self):
        self.base_url = Config.ACCOUNTING_API_BASE_URL.rstrip('/')
        self.headers = {
            "X-API-Key": Config.ACCOUNTING_API_KEY,
            "Content-Type": "application/json"
        }

    def health(self) -> dict:
        response = requests.get(
            f"{self.base_url}/health",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_partners(self) -> list[dict]:
        return self._get("/partners")["data"]["partners"]

    def get_tax_codes(self) -> list[dict]:
        return self._get("/tax-codes")["data"]["tax_codes"]

    def register_invoice(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/invoices",
            headers=self.headers,
            json=payload,
            timeout=30
        )

        body = response.json()

        if response.status_code >= 400:
            error = body.get("error") or {}

            raise AccountingAPIError(
                status_code = response.status_code,
                code = error.get("code"),
                message = error.get("message", "Unknown accounting API error"),
                details = error.get("details")
            )

        return body["data"]

    def _get(self, path: str) -> dict:
        response = requests.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()