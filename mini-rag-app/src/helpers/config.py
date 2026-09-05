from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str 
    VERSION: str 
    OPENAI_API_KEY: str
    FILE_ALLOWED_EXTENSIONS: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()

