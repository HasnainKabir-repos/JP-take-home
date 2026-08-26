import math
import re
from datetime import date
from typing import Optional

from app.models import (
    NormalizedInvoice,
    NormalizedLine,
    RawExtraction,
)
from app.services.accounting_client import AccountingClient
from app.services.partner_matcher import PartnerMatcher


ERA_START_YEAR = {
    "令和": 2018,
    "平成": 1988,
}


def normalize_date(raw_date: str) -> str:
    if not raw_date:
        raise ValueError("DATE_MISSING")

    value = raw_date.strip()

    # Example: 2026年1月7日
    match = re.search(
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        value,
    )

    if match:
        year, month, day = map(int, match.groups())
        return date(year, month, day).isoformat()

    # Example: 令和8年1月7日
    match = re.search(
        r"(令和|平成)\s*(\d+|元)\s*年\s*"
        r"(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        value,
    )

    if match:
        era, era_year, month, day = match.groups()

        era_year = 1 if era_year == "元" else int(era_year)
        year = ERA_START_YEAR[era] + era_year

        return date(
            year,
            int(month),
            int(day),
        ).isoformat()

    # Examples: 2026-01-07, 2026/01/07, 2026.01.07
    match = re.search(
        r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})",
        value,
    )

    if match:
        year, month, day = map(int, match.groups())
        return date(year, month, day).isoformat()

    raise ValueError(
        f"DATE_NORMALIZATION_FAILED: {raw_date}"
    )


class InvoiceNormalizer:
    def __init__(
        self,
        partner_matcher: PartnerMatcher,
        accounting_client: AccountingClient,
    ):
        self.partner_matcher = partner_matcher
        self.accounting_client = accounting_client

    def get_tax_code_map(self) -> dict[str, float]:
        """
        Load tax codes and rates from the authoritative accounting API.
        """

        tax_codes = self.accounting_client.get_tax_codes()

        return {
            tax_code["tax_code"]: float(tax_code["rate"])
            for tax_code in tax_codes
        }

    def resolve_tax_code(
        self,
        tax_rate_text: Optional[str],
        tax_code_rates: dict[str, float],
    ) -> str:
        """
        Convert the visible invoice tax rate into an accounting-system
        tax code using the API's tax-code master.
        """

        if not tax_rate_text:
            raise ValueError("TAX_RATE_MISSING")

        normalized = (
            tax_rate_text
            .strip()
            .replace(" ", "")
            .replace("％", "%")
        )

        if not normalized.endswith("%"):
            raise ValueError(
                f"UNSUPPORTED_TAX_RATE: {tax_rate_text}"
            )

        try:
            percentage = float(
                normalized.removesuffix("%")
            )
        except ValueError as exc:
            raise ValueError(
                f"UNSUPPORTED_TAX_RATE: {tax_rate_text}"
            ) from exc

        extracted_rate = percentage / 100

        for tax_code, api_rate in tax_code_rates.items():
            if api_rate == extracted_rate:
                return tax_code

        raise ValueError(
            f"UNKNOWN_TAX_RATE: {tax_rate_text}"
        )

    def normalize(
        self,
        raw: RawExtraction,
    ) -> NormalizedInvoice:

        # --------------------------------------------------
        # 1. Resolve partner against accounting master data
        # --------------------------------------------------

        partner = self.partner_matcher.resolve(
            supplier_name=raw.supplier_name,
            registration_no=raw.registration_no,
        )

        if not partner:
            raise ValueError("PARTNER_UNRESOLVED")

        if not raw.invoice_number:
            raise ValueError("INVOICE_NUMBER_MISSING")

        # --------------------------------------------------
        # 2. Normalize dates
        # --------------------------------------------------

        issue_date = normalize_date(raw.issue_date_raw)
        due_date = normalize_date(raw.due_date_raw)

        # --------------------------------------------------
        # 3. Load authoritative tax configuration
        # --------------------------------------------------

        tax_code_rates = self.get_tax_code_map()

        # --------------------------------------------------
        # 4. Resolve invoice-level tax summaries
        # --------------------------------------------------

        if not raw.taxes:
            raise ValueError("TAX_RATE_MISSING")

        if len(raw.taxes) != 1:
            raise ValueError(
                "MULTIPLE_TAX_GROUPS_REQUIRE_REVIEW"
            )

        invoice_tax = raw.taxes[0]

        invoice_tax_code = self.resolve_tax_code(
            invoice_tax.tax_rate_text,
            tax_code_rates,
        )

        # --------------------------------------------------
        # 5. Normalize lines
        # --------------------------------------------------

        normalized_lines = []

        for line in raw.lines:
            normalized_lines.append(
                NormalizedLine(
                    description=line.description,
                    quantity=line.quantity,
                    unit=line.unit or "unit",
                    unit_price=line.unit_price,
                    amount=line.amount,
                    tax_code=invoice_tax_code,
                )
            )

        if not normalized_lines:
            raise ValueError("NO_LINES_EXTRACTED")

        # --------------------------------------------------
        # 6. Deterministically recompute subtotal
        # --------------------------------------------------

        subtotal = sum(
            line.amount
            for line in normalized_lines
        )

        # --------------------------------------------------
        # 7. Group subtotal by tax code
        # --------------------------------------------------

        subtotal_by_tax_code = {}

        for line in normalized_lines:
            subtotal_by_tax_code[line.tax_code] = (
                subtotal_by_tax_code.get(
                    line.tax_code,
                    0,
                )
                + line.amount
            )

        # --------------------------------------------------
        # 8. Recompute tax exactly from API tax rates
        #
        # floor(group_subtotal × rate)
        # --------------------------------------------------

        tax_amount = sum(
            math.floor(
                group_subtotal
                * tax_code_rates[tax_code]
            )
            for tax_code, group_subtotal
            in subtotal_by_tax_code.items()
        )

        # --------------------------------------------------
        # 9. Recompute total
        # --------------------------------------------------

        total_amount = subtotal + tax_amount

        return NormalizedInvoice(
            partner_code=partner["partner_code"],
            invoice_number=raw.invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            currency="JPY",
            lines=normalized_lines,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
        )