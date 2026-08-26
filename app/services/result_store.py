import json
from datetime import datetime
from pathlib import Path

from app.models import ProcessingResult


class ResultStore:
    def __init__(self, base_dir: str = "results"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        result: ProcessingResult,
    ) -> Path:
        filename = (
            f"{Path(result.filename).stem}.json"
        )

        output_path = (
            self.base_dir / filename
        )

        payload = {
            "processed_at": (
                datetime.now().isoformat()
            ),
            **result.model_dump(),
        }

        output_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        return output_path