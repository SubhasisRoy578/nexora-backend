from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================
    # DATABASE
    # =========================================
    DATABASE_URL: str

    # =========================================
    # AUTH
    # =========================================
    SECRET_KEY: str = "supersecretkey"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # =========================================
    # AI API KEYS
    # =========================================
    GEMINI_API_KEY: str = "AIzaSyCieUfu0s7Teh_PoUWYPu_nIzLXfqhcpto"

    GROQ_API_KEY: str = "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"

    OPENROUTER_API_KEY: str = "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"

    TAVILY_API_KEY: str = "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"

    HUGGINGFACE_API_KEY: str = "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"

    ELEVENLABS_API_KEY: str = ""

    # =========================================
    # CLERK AUTH
    # =========================================
    CLERK_SECRET_KEY: str = ""

    # =========================================
    # VECTOR DB
    # =========================================
    CHROMA_DB_DIR: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()