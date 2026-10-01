"""
Settings - saare environment-dependent values (DB URL, Redis URL, model paths)
yahan se load hote hain, .env file se ya environment variables se. Pydantic
Settings isliye (raw os.environ nahi) kyunki type validation + defaults + ek
hi jagah documentation milta hai.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # +psycopg2 explicit hai - SQLAlchemy 2.1 me bare "postgresql://" ab
    # psycopg (v3) dialect ko default pick karta hai, chahe psycopg2-binary
    # install ho (real bug, apni sandbox me reproduce karke confirm kiya).
    database_url: str = "postgresql+psycopg2://invoice:invoice@localhost:5432/invoice"
    redis_url: str = "redis://localhost:6379/0"

    upload_dir: str = "data/uploads"
    sample_data_dir: str = "data/samples"

    # Inference backend: "pytorch_gpu" | "pytorch_cpu" | "onnx_int8" | "dummy"
    # "dummy" sirf testing/CI ke liye - real model load nahi karta, fixed
    # fake result deta hai, taaki GPU/model checkpoint ke bina bhi tests
    # chal sakein.
    inference_backend: str = "pytorch_gpu"
    lora_adapter_dir: str = "models/lora_combined_v1"
    onnx_int8_path: str = "models/onnx/model_int8.onnx"

    # Tesseract ka binary (Python package "pytesseract" sirf ek wrapper hai -
    # asli OCR engine ye alag se install hota hai, system PATH me hona
    # chahiye). Windows pe installer PATH me add nahi karta agar box uncheck
    # ho, aur already-open terminals updated PATH bhi nahi dekhte - isliye
    # explicit override yahan diya ja sakta hai (env var TESSERACT_CMD).
    # None = auto-detect: pehle PATH check, phir Windows ka standard install
    # path fallback (src/api/inference.py me).
    tesseract_cmd: str | None = None

    max_upload_mb: int = 10
    allowed_extensions: tuple = (".png", ".jpg", ".jpeg")


settings = Settings()
