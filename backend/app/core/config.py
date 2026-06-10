from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "more_ai"
    env: str = "development"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

settings = Settings()