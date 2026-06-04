from pyexplorer_api.core.config import Settings


def make_test_settings() -> Settings:
    return Settings(realtime_enabled=False)
