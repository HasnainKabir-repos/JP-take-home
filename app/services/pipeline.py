from pathlib import Path
from app.models import ProcessingResult
from app.services.accounting_client import (
    AccountingAPIError,
    AccountingClient,
)
from app.services.extractor import InvoiceExtractor
from app.services.normalizer import InvoiceNormalizer
from app.services.verifier import InvoiceVerifier
from app.services.result_store import ResultStore
class InvoicePipeline:

    def __init__(
        self,
        extractor: InvoiceExtractor,
        normalizer: InvoiceNormalizer,
        verifier: InvoiceVerifier,
        accounting_client: AccountingClient,
        result_store: ResultStore
    ):
        self.extractor = extractor
        self.normalizer = normalizer
        self.verifier = verifier
        self.accounting_client = accounting_client
        self.result_store = result_store

    def process(
        self,
        file_path: str,
    ) -> ProcessingResult:

        filename = Path(file_path).name

        try:
            raw = self.extractor.extract(
                file_path
            )
            print(f"[{filename}] Extraction complete")
            print(f"[{filename}] Starting normalization")
        except Exception as exc:
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="EXTRACTION_FAILED",
                    error_message=str(exc),
                )
            )

        try:
            normalized = self.normalizer.normalize(
                raw
            )

            print(f"[{filename}] Normalization complete")
            print(f"[{filename}] Starting verification")
        except ValueError as exc:
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="NEEDS_REVIEW",
                    raw_extraction=raw,
                    error_code=str(exc),
                    error_message=str(exc),
                )
            )

        verification = self.verifier.verify(
            raw,
            normalized,
        )
        print(f"[{filename}] Verification complete")
        print(f"[{filename}] Registering invoice")

        if not verification.passed:
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="NEEDS_REVIEW",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    error_code="VERIFICATION_FAILED",
                    error_message="; ".join(
                        verification.errors
                    ),
                )
            )

        try:
            result = (
                self.accounting_client
                .register_invoice(
                    normalized.model_dump()
                )
            )
            print(f"[{filename}] Registration complete")
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="REGISTERED",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    accounting_result=result,
                )
            )

        except AccountingAPIError as exc:
            return self._handle_api_error(
                filename,
                raw,
                normalized,
                verification,
                exc,
            )

    def _handle_api_error(
        self,
        filename,
        raw,
        normalized,
        verification,
        error,
    ) -> ProcessingResult:

        # Idempotent outcome.
        if error.code == "DUPLICATE_INVOICE":
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="ALREADY_REGISTERED",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    error_code=error.code,
                    error_message=error.message,
                )
            )

        # Strong extraction-quality signal.
        if error.code == "AMOUNT_MISMATCH":
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="NEEDS_REVIEW",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    error_code=error.code,
                    error_message=error.message,
                )
            )
           
        # Indicates our deterministic tax mapping
        # has diverged from the accounting master.
        if error.code == "UNKNOWN_TAX_CODE":
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="SYSTEM_ERROR",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    error_code=error.code,
                    error_message=error.message,
                )
            )
            
        if error.code == "DUE_DATE_BEFORE_ISSUE_DATE":
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="NEEDS_DATE_REVIEW",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    error_code=error.code,
                    error_message=error.message,
                )
            )
            
        if error.code == "PARTNER_NOT_FOUND":
            return self._finish(
                ProcessingResult(
                    filename=filename,
                    status="NEEDS_PARTNER_REPAIR",
                    raw_extraction=raw,
                    normalized_invoice=normalized,
                    verification=verification,
                    error_code=error.code,
                    error_message=error.message,
                )
            )
            
        return self._finish(
            ProcessingResult(
                filename=filename,
                status="SYSTEM_ERROR",
                raw_extraction=raw,
                normalized_invoice=normalized,
                verification=verification,
                error_code=error.code,
                error_message=error.message,
            )
        )
        
    def _finish(
        self,
        result: ProcessingResult,
    ) -> ProcessingResult:
        self.result_store.save(result)
        return result