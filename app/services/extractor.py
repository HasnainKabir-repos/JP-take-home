import json
import mimetypes
from pathlib import Path

from google import genai
from google.genai import types

from app.config import Config
from app.models import RawExtraction

EXTRACTION_PROMPT = """
You are an invoice-reading component in an accounting automation system.

Your task is to READ the supplied Japanese invoice and extract ONLY information
that is visibly supported by the document.

You are not an accountant and must NOT:
- invent missing values
- calculate totals
- calculate tax
- infer partner codes
- infer accounting tax codes
- fix arithmetic inconsistencies
- guess unclear digits

Return JSON matching this exact structure:

{
  "supplier_name": string | null,
  "registration_no": string | null,
  "invoice_number": string | null,
  "issue_date_raw": string | null,
  "due_date_raw": string | null,
  "currency": "JPY" | null,
  "lines": [
    {
      "description": string,
      "quantity": integer | null,
      "unit": string | null,
      "unit_price": integer | null,
      "amount": integer,
    }
  ],
  "taxes": [
    {
      "tax_rate_text": string,
      "taxable_amount": integer | null,
      "tax_amount": integer | null
    }
  ],
  "printed_subtotal": integer | null,
  "printed_tax_amount": integer | null,
  "printed_total_amount": integer | null
}

Rules:

1. Extract values exactly as supported by the document.
2. Preserve Japanese era dates as printed. Do not convert them.
3. Remove currency symbols and thousands separators from numeric values.
4. Return numbers as integers where the document clearly provides them.
5. If a value cannot be read confidently, return null rather than guessing.
6. Every line must correspond to an actual invoice line.
7. Do not combine or split lines unless the document clearly represents them that way.
8. If tax is shown per line, attach the visible rate to that line.
9. If a tax rate applies to the whole invoice and is not line-specific,
   use that rate for each applicable line only when the document makes
   that relationship explicit.
10. Printed subtotal, tax, and total are evidence from the invoice.
    Do not recompute them.
11. Tax information may appear at invoice level rather than per line.

IMPORTANT TAX EXTRACTION RULE:

Tax information may appear separately from the line-item table.

Look for tax summaries anywhere on the invoice, including text such as:

"消費税 10%（対象 304,000）"
followed by:
"30,400"

For this example extract:

"taxes": [
  {
    "tax_rate_text": "10%",
    "taxable_amount": 304000,
    "tax_amount": 30400
  }
]

Do not omit the "taxes" field when tax information is visible.

Do not calculate tax values. Only extract what is visibly printed.
"""

class InvoiceExtractor:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=Config.GOOGLE_CLOUD_PROJECT,
            location=Config.GOOGLE_CLOUD_LOCATION
        )

    def extract(self, file_path: str) -> RawExtraction:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Invoice file not found: {path}")

        mime_type = self._get_mime_type(path)
        file_bytes = path.read_bytes()

        response = self.client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type
                ),
                EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0
            )
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response")
        
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned invalid JSON: {response.text}"
            ) from exc

        return RawExtraction.model_validate(data)

    @staticmethod
    def _get_mime_type(path:Path) -> str:
        mime_type, _ = mimetypes.guess_type(path.name)

        supported = {
            "application/pdf",
            "image/jpeg"
        }

        if mime_type not in supported:
            raise ValueError(
                f"Unsupported invoice type: {mime_type}"
            )

        return mime_type