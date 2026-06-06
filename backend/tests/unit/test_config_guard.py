"""Production startup guard: refuse insecure defaults when ENV=prod."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import _DEFAULT_JWT_SECRET, Settings


class TestProdSecretGuard:
    def test_default_jwt_secret_rejected_in_prod(self):
        with pytest.raises(ValidationError):
            Settings(ENV="prod", JWT_SECRET_KEY=_DEFAULT_JWT_SECRET)

    def test_short_jwt_secret_rejected_in_prod(self):
        with pytest.raises(ValidationError):
            Settings(ENV="prod", JWT_SECRET_KEY="too-short")

    def test_wildcard_cors_rejected_in_prod(self):
        with pytest.raises(ValidationError):
            Settings(
                ENV="prod",
                JWT_SECRET_KEY="a" * 40,
                CORS_ORIGINS="*",
            )

    def test_strong_config_accepted_in_prod(self):
        s = Settings(
            ENV="prod",
            JWT_SECRET_KEY="x" * 48,
            CORS_ORIGINS="https://app.example.com",
        )
        assert s.ENV == "prod"

    def test_defaults_fine_in_dev(self):
        # The committed default secret is acceptable outside prod.
        s = Settings(ENV="dev")
        assert s.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET
