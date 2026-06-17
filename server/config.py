from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Nexora AI"
    DEBUG: bool = True

    OPENAI_API_KEY: str = ""

    DATABASE_URL: str = "sqlite:///./nexora.db"

    SECRET_KEY: str = "supersecretkey"

    CHROMA_DB_DIR: str = "./chroma_db"

    CLERK_SECRET_KEY: str = ""

    ELEVENLABS_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()