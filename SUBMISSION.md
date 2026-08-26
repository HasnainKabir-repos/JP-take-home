# Submission

- Name: A Z Hasnain Kabir
- Submission date (YYYY-MM-DD): 2026-08-27
- Hours actually spent: 8
- Repository / how to run it: https://github.com/HasnainKabir-repos/JP-take-home

## 1. Understanding the request

The client wants me to integrate AI into their system to create a document workflow that replaces the human effort of entering invoices manually. Also, the client wants me to work out a way to verify if the extracted data is correct.

Problem:
Needs to insert invoice data manually into accounting system and sometimes typos occur that are dangerous.

Solution:
AI should handle data insertion and self-verify its own output.

## 2. What you would have asked the client

| What you wanted to ask | The assumption you made | Why |
|---|---|---|
| Is there a cost limit for handling each of the invoices? | Yes | Client may need to handle hundreds of invoices per month so having a cost limit is natural. |
| Should I implement a manual review UI for low-confidence or failed validation invoices? | Yes | For invoices with poor resolution or barely visible parts, it is necessary for human intervention. We cannot be 100% confident on AI generated outputs despite the model capacity. |

## 3. Scoping decisions

**What you built**
An AI powered document parser that generates raw data based on a document and the data is parsed and converted to normalized data which is then recalculated and compared with given data as well as validated with the data present in `accounting_api.py`.

**What you left out, and why**
Some information will need review. I did not have time to implement that part. 

## 4. Design and technology choices

```

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

LLM reads the invoice for supplier information, invoice number, dates, lines, tax, printed totals, etc. It does no accounting calculations. After that, python code resolves suppliers, maps tax rates, normalizes dates and recomputes financial values using the provided Accounting API. So, number of decisions deligated to the model is reduced.

Technology choices: Python, as this assignment is an orchestration and data-processing problem. Google `gemini-2.5-flash` was used as an LLM to parse the documents. The model is supposed to be vision-capable and can handle selectable-text PDFs. Used `pydantic` for parsing AI output before calculating it. I deliberately decided against relying on the calculated total provided inside documents so I deterministictly calculated the subtoal and total of the values as well as tax by tax-code group using the API's rates and flooring rule. 

**Decided Against**: 
Google Document AI, even though it has a prebuilt invoice parser, the main engineering challenge of this assignment is not simply obtaining invoice fields. 

LLM should not perform accounting logic. LLMs are non-deterministic.

A human-review UI screen would have been very useful but I decided its not worth the time for this challenge.

**Used LLM**
I used `gemini-2.5-flash`with Google Agent API Platforn as I have a free tier with google cloud platform.

## 5. How you used AI, and how you checked it

**What you delegated to AI**
At first, told AI to explain the `accounting_api.py` code, the http methods to fully understand what I am dealing with. Based on the fields available, I created the validation classes using AI. Created the prompt for LLM with the help of AI. Created normalizer and error handling code with AI. Also created a powershell script to run the entire thing.

**How you verified the output**
I drew a function call trace from route function call to the end in my notebook and traced each function one by one to check which operations are getting executed. Also spent time on code review.

**A case where the AI got it wrong** (one example is enough, if you have one)
When creating the prompt and model schema, it incorrectly assumed tax rates to be present at every line. Had to fix it. Also had to fix normalization code, it replaced some japanese words in normalization stage with empty space. Had to remove it as well.
## 6. Integrating with the accounting system

| Invoice | Result | How you handled it |
|---|---|---|
| Invoice_01.pdf | REGISTERED | Extracted and normalized successfully |
| Invoice_02.pdf | REGISTERED | Extracted and normalized successfully |
| Invoice_03.pdf | NEEDS_REVIEW | Multiple tax rates detected. The pipeline stopped rather than guessing. Needs human review. |
| Invoice_04.jpg | REGISTERED | Extracted and normalized successfully |
| Invoice_05.jpg | REGISTERED | Extracted and normalized successfully |
| Invoice_06.jpg | REGISTERED | Extracted and normalized successfully |
| Invoice_07.jpg | ALREADY_REGISTERED | Detected duplicate invoice. Treated as idempotent outcome than a failure |
| Invoice_08.jpg | NEEDS_REVIEW | Multiple tax rates detected. The pipeline stopped rather than guessing. Needs human review. |
| Invoice_09.pdf | NEEDS_REVIEW | Pipeline computed total and found mismatch with the printed total. Stopped rather than guessing. Needs human review |
| Invoice_10.jpg | NEEDS_REVIEW | Could not find supplier name. Pipeline stopped rather than guessing. Needs human review. |
| Invoice_11.jpg | REGISTERED | Extracted and normalized successfully |
| Invoice_12.jpg | REGISTERED | Extracted and normalized successfully |
## 7. Cost, limits, and risk in production

- **Cost per invoice** (and what makes it up):
Roughly $0.0003 per image input and $0.00125 per image text output. So, my estimate $0.002.
- **Monthly cost at 1,000 invoices per month**:
My estimate: $2 per month
- **Processing time per invoice**:
2.5 seconds
- **Where this breaks first**:
Error: Resource Exhausted. This happens sometimes for gemini.
- **How you would find out if something was registered incorrectly**:
I will need to run automated deterministic logic checks like checking if the line sum equals to subtotal, checking if taxable amount calculated is equal to the tax amount present and the grand total. Cross-referencing flags would help here.
## 8. What you would do with another 8 hours

1. Build human review workflow which will show original invoice along with extracted fields allowing a reviewer to correct only certain values and resubmit.
2. For failed invoices, I would improve recovery methods. For fields that have failed in extraction, a recovery extraction focusing on only those fields would help.
3. Should add traces and metrics for extraction success rate, verification failures, latency and restimated model cost per invoice.

**Why this order:** first improve safety, then reduce number of cases needing that safety review and finally optimize and monitor system for production use.
