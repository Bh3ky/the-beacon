import os

import pytest
import rifthub_backend.config as config_module


@pytest.fixture(autouse=True)
def isolate_rifthub_env(monkeypatch):
    for name in [name for name in os.environ if name.startswith("RIFTHUB_")]:
        monkeypatch.delenv(name)
    monkeypatch.setattr(config_module, "_DOTENV_LOADED", True)
    monkeypatch.setenv(
        "RIFTHUB_DATABASE_URL",
        "postgresql+asyncpg://user:pass@127.0.0.1:5432/rifthub_test",
    )
