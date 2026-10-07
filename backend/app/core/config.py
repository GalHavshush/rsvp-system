from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://rsvp:rsvp@localhost/rsvp"
    cookie_secure: bool = False
    session_days: int = 30
    default_region: str = "IL"
    messaging_provider: str = "test_csv"


settings = Settings()
