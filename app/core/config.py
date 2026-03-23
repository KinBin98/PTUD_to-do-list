from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    app_name: str = "To-Do API"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    model_config = ConfigDict(env_file=".env")


settings = Settings()
