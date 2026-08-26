from datetime import date

from app.models import (
    NormalizedInvoice,
    RawExtraction,
    VerificationResult,
)


class InvoiceVerifier:

    def verify(
        self,
        raw: RawExtraction,
        normalized: NormalizedInvoice,
    ) -> VerificationResult:

        errors = []
        warnings = []

        # Check 1:
        # extracted lines must agree with the printed subtotal
        if raw.printed_subtotal is not None:
            if (
                normalized.subtotal
                != raw.printed_subtotal
            ):
                errors.append(
                    "LINE_SUBTOTAL_MISMATCH: "
                    f"sum(lines)={normalized.subtotal}, "
                    f"printed_subtotal="
                    f"{raw.printed_subtotal}"
                )

        # Check 2:
        # deterministic tax must agree with printed tax
        if raw.printed_tax_amount is not None:
            if (
                normalized.tax_amount
                != raw.printed_tax_amount
            ):
                errors.append(
                    "TAX_MISMATCH: "
                    f"computed={normalized.tax_amount}, "
                    f"printed={raw.printed_tax_amount}"
                )

        # Check 3:
        # deterministic total must agree with printed total
        if raw.printed_total_amount is not None:
            if (
                normalized.total_amount
                != raw.printed_total_amount
            ):
                errors.append(
                    "TOTAL_MISMATCH: "
                    f"computed={normalized.total_amount}, "
                    f"printed={raw.printed_total_amount}"
                )

        # Check 4:
        # basic business date sanity
        if (
            date.fromisoformat(normalized.due_date)
            < date.fromisoformat(normalized.issue_date)
        ):
            errors.append(
                "DUE_DATE_BEFORE_ISSUE_DATE"
            )

        # Evidence warning rather than failure.
        if raw.registration_no is None:
            warnings.append(
                "Registration number not found; "
                "partner resolved from name/alias."
            )

        return VerificationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )