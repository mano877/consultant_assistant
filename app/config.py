import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
LEADS_ADMIN_TOKEN: str = os.getenv("LEADS_ADMIN_TOKEN", "")
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
if any("*" in origin for origin in ALLOWED_ORIGINS):
    raise ValueError("ALLOWED_ORIGINS must contain explicit origins, not wildcards")
