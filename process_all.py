import json
from pathlib import Path

from app.services.factory import create_pipeline


INVOICES_DIR = Path("invoices")
OUTPUT_DIR = Path("results")
OUTPUT_FILE = OUTPUT_DIR / "batch_results.json"


def main():
    pipeline = create_pipeline()

    OUTPUT_DIR.mkdir(exist_ok=True)

    invoice_files = sorted(
        file
        for file in INVOICES_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower()
        in {".pdf", ".jpg"}
    )

    if not invoice_files:
        print("No invoice files found.")
        raise SystemExit(1)

    results = []

    print(
        f"Found {len(invoice_files)} invoice(s)\n"
    )

    for index, invoice_path in enumerate(
        invoice_files,
        start=1,
    ):
        print(
            f"[{index}/{len(invoice_files)}] "
            f"Processing {invoice_path.name}"
        )

        try:
            result = pipeline.process(
                str(invoice_path)
            )

            result_data = result.model_dump()

            results.append(result_data)

            print(
                f"    Status: "
                f"{result_data['status']}"
            )

        except Exception as exc:
            print(
                f"    FAILED: {exc}"
            )

            result_data = {
                "filename": invoice_path.name,
                "status": "NEEDS_REVIEW",
                "raw_extraction": None,
                "normalized_invoice": None,
                "verification": None,
                "accounting_result": None,
                "error_code": "PROCESSING_EXCEPTION",
                "error_message": str(exc),
            }

            results.append(result_data)

        # Save progress after every invoice.
        # This preserves completed results if a later
        # invoice or model request fails.
        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                results,
                file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

    print("\n" + "=" * 40)
    print("PROCESSING COMPLETE")
    print("=" * 40)

    registered = sum(
        result["status"] == "REGISTERED"
        for result in results
    )

    already_registered = sum(
        result["status"] == "ALREADY_REGISTERED"
        for result in results
    )

    needs_review = sum(
        result["status"] == "NEEDS_REVIEW"
        for result in results
    )

    print(f"Total:              {len(results)}")
    print(f"Registered:         {registered}")
    print(
        f"Already registered: "
        f"{already_registered}"
    )
    print(f"Needs review:       {needs_review}")

    print(
        f"\nDetailed results saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()