from app.services.accounting_client import (
    AccountingClient,
)
from app.services.extractor import (
    InvoiceExtractor,
)
from app.services.normalizer import (
    InvoiceNormalizer,
)
from app.services.partner_matcher import (
    PartnerMatcher,
)
from app.services.pipeline import (
    InvoicePipeline,
)
from app.services.verifier import (
    InvoiceVerifier,
)

from app.services.result_store import ResultStore

def create_pipeline() -> InvoicePipeline:

    accounting_client = AccountingClient()

    partner_matcher = PartnerMatcher(
        accounting_client
    )

    normalizer = InvoiceNormalizer(
        partner_matcher=partner_matcher,
        accounting_client=accounting_client
    )

    verifier = InvoiceVerifier()
    extractor = InvoiceExtractor()
    result_store = ResultStore()

    return InvoicePipeline(
        extractor=extractor,
        normalizer=normalizer,
        verifier=verifier,
        accounting_client=accounting_client,
        result_store=result_store
    )