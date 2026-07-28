from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App Config
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Keys
    APIFY_API_TOKEN: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    OPEN_ROUTER_API_KEY: str = Field(default="")
    MISTRAL_API_KEY: str = Field(default="")
    
    # Auth (Google)
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    JWT_SECRET_KEY: str = Field(default="dev_secret_key_change_in_prod")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5434/pathlight")
    
    # Observability
    LANGFUSE_SECRET_KEY: str = Field(default="")
    LANGFUSE_PUBLIC_KEY: str = Field(default="")
    LANGFUSE_BASE_URL: str = Field(default="https://us.cloud.langfuse.com")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()
