from pydantic_settings import BaseSettings, SettingsConfigDict

API_TOKEN = "your_api_token"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int = 0
    API_HASH: str = 'XXXXXXXXXXXX'

    MIN_AVAILABLE_ENERGY: int = 100
    SLEEP_BY_MIN_ENERGY: int = 200

    ADD_TAPS_ON_TURBO: int = 2500

    AUTO_UPGRADE_TAP: bool = True
    MAX_TAP_LEVEL: int = 12
    AUTO_UPGRADE_ENERGY: bool = True
    MAX_ENERGY_LEVEL: int = 12
    AUTO_UPGRADE_CHARGE: bool = True
    MAX_CHARGE_LEVEL: int = 3

    APPLY_DAILY_ENERGY: bool = True
    APPLY_DAILY_TURBO: bool = True

    RANDOM_TAPS_COUNT: list[int] = [15, 100]
    SLEEP_BETWEEN_TAP: list[int] = [38, 50]

    USE_PROXY_FROM_FILE: bool = True

    USE_TAP_BOT: bool = False
    EMERGENCY_STOP: bool = False


settings = Settings()
