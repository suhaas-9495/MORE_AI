from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    app_name: str = "more_ai"
    env: str = "development"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    langfuse_public_key: str = "sk-lf-8acd87f3-20a9-48d1-aee3-c36d7315de25"
    langfuse_secret_key: str = "pk-lf-05fcd09e-aa48-4098-92d8-ecf0a9bd0ba3"
    langfuse_host: str = "https://cloud.langfuse.com"
    


settings = Settings()