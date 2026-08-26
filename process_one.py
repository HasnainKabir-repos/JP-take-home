import json
import sys

from app.services.factory import create_pipeline


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python process_one.py <invoice_path>"
        )
        raise SystemExit(1)

    invoice_path = sys.argv[1]

    pipeline = create_pipeline()

    result = pipeline.process(invoice_path)

    print(
        json.dumps(
            result.model_dump(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()