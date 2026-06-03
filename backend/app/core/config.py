from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "NexusAI"
    env: str = "development"
    
    # Groq settings (instead of Ollama)
    groq_api_key: str = ""  # Will come from .env
    groq_model: str = "llama-3.3-70b-versatile"  # Fastest Groq model
    
    # Optional: Tavily for web search
    tavily_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()