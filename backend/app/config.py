from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/debit_optimiseur"
    storage_path: str = "../storage/pdfs"

    panel_width: int = 2800
    panel_height: int = 2070
    kerf: int = 3
    border_margin: int = 5


settings = Settings()
