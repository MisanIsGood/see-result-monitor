from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./see_monitor.db"
    CORS_ORIGINS: str = "http://localhost:5173,https://your-frontend.onrender.com"
    MONITOR_INTERVAL_SECONDS: int = 60
    ENVIRONMENT: str = "production"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()