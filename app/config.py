import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ACCOUNTING_API_BASE_URL = os.getenv(
        "ACCOUNTING_API_BASE_URL",
        "http://localhost:8080",
    )

    ACCOUNTING_API_KEY = os.getenv(
        "ACCOUNTING_API_KEY",
        "demo-key-1234",
    )

    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = os.getenv(
        "GOOGLE_CLOUD_LOCATION",
        "global",
    )

    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )