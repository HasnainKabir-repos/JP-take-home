import re
import unicodedata
from typing import Optional
from app.services.accounting_client import AccountingClient

def normalize_text(value:str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()

class PartnerMatcher:
    def __init__(self, accounting_client: AccountingClient):
        self.client = accounting_client

    def resolve(
        self,
        supplier_name: Optional[str],
        registration_no: Optional[str]
    ) -> Optional[dict]:
        partners = self.client.get_partners()

        if registration_no:
            normalized_registration = registration_no.replace(" ", "")

            for partner in partners:
                if (
                    partner["registration_no"]
                    .replace(" ", "")
                    == normalized_registration
                ):
                    return partner

        if supplier_name:
                normalized_supplier = normalize_text(supplier_name)

                matches = []

                for partner in partners:
                    candidates = [
                        partner["name"],
                        *partner.get("aliases", []),
                    ]

                    for candidate in candidates:
                        if (
                            normalize_text(candidate)
                            == normalized_supplier
                        ):
                            matches.append(partner)
                            break

                if len(matches) == 1:
                    return matches[0]

                return None
