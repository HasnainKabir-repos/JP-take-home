# AI Invoice Processing Agent

An AI-powered invoice processing workflow that reads Japanese invoices, converts them into structured accounting data, verifies the extracted values with deterministic checks, and registers valid invoices with a mock accounting system.

The project was built for an **AI Agent Engineer take-home assignment**.

## What it does

For each invoice, the pipeline:

1. Reads a PDF or scanned image using Gemini via Vertex AI.
2. Extracts supplier information, invoice number, dates, line items, tax information, and printed totals.
3. Validates the AI output against Pydantic models.
4. Resolves the supplier against the accounting API's partner master data.
5. Resolves tax rates against the accounting API's tax-code master data.
6. Normalizes dates into the format required by the API.
7. Recomputes subtotal, tax, and total deterministically.
8. Verifies computed values against the values printed on the invoice.
9. Registers valid invoices with the accounting API.
10. Stops safely and returns `NEEDS_REVIEW` when the invoice cannot be handled reliably.

The LLM reads the document. Deterministic code handles accounting rules.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │ Invoice file         │
                    │ PDF / scanned image  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Gemini via Vertex AI │
                    │ Multimodal extraction│
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ RawExtraction        │
                    │ AI observation only  │
                    └──────────┬──────────┘
                               ↓
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
   Partner resolution    Date normalization    Tax resolution
   against API master    deterministic         against API
   data                                         tax master
          └────────────────────┼────────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Deterministic layer  │
                    │ recomputes amounts   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Verification         │
                    │ printed vs computed  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Accounting API       │
                    └──────────┬──────────┘
                               ↓
              ┌────────────────┼────────────────┐
              ↓                ↓                ↓
          REGISTERED      ALREADY           NEEDS_REVIEW
                         REGISTERED
```
## Why this design?

The accounting API is treated as authoritative.

The LLM is responsible for reading the invoice, but it is not trusted to:

- perform accounting calculations;
- invent partner codes;
- invent tax codes;
- decide how API errors should be handled.

Instead, the deterministic layer:

- resolves suppliers using API partner master data;
- maps visible tax rates to API tax codes;
- normalizes dates;
- calculates subtotal from extracted line amounts;
- calculates tax using the API's rates and flooring rules;
- calculates the final total.

This reduces the number of important decisions delegated to a non-deterministic model.

## Quick start
### Prerequisites
- Python 3.11+
- Google Cloud project with Vertex AI enabled
- Google Cloud authentication configured locally
- PowerShell on Windows

Install dependencies:

```powershell
pip install -r requirements.txt
```

Authenticate with Google Cloud:

```powershell
gcloud auth application-default login
```

Set your Google Cloud project ID:

```powershell
$env:GOOGLE_CLOUD_PROJECT="your-project-id"
```

Set the Vertex AI location if required:

```powershell
$env:GOOGLE_CLOUD_LOCATION="us-central1"
```
## Processing an individual invoice

For debugging or development, an individual invoice can be processed with:

```powershell
python process_one.py .\invoices\invoice_01.pdf
```

### Process everything
The project includes a PowerShell script that starts the accounting API and runs the invoice processing workflow.

```powershell
.\run.ps1
```

This is the intended single-command entry point for the assignment.

The script:

1. Starts the mock accounting API.
2. Starts the application.
3. Processes the supplied invoices.
4. Prints or saves the processing results.

