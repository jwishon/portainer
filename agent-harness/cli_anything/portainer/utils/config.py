"""Configuration for cli-anything-portainer."""

import json
import os
from pathlib import Path


class ConfigError(Exception):
    pass


class Config:
    DEFAULT_CONFIG_FILE = Path.home() / ".config" / "cli-anything-portainer" / "config.json"

    def __init__(self, config_path: Path = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_FILE
        self._data: dict = {}
        self._load()

    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=2)

    @property
    def url(self) -> str:
        return os.environ.get("PORTAINER_URL", self._data.get("url", "")).rstrip("/")

    @url.setter
    def url(self, v: str):
        self._data["url"] = v.rstrip("/")

    @property
    def username(self) -> str:
        return os.environ.get("PORTAINER_USER", self._data.get("username", ""))

    @username.setter
    def username(self, v: str):
        self._data["username"] = v

    @property
    def password(self) -> str:
        return os.environ.get("PORTAINER_PASSWORD", self._data.get("password", ""))

    @password.setter
    def password(self, v: str):
        self._data["password"] = v

    @property
    def token(self) -> str:
        """Cached JWT from last login."""
        return os.environ.get("PORTAINER_TOKEN", self._data.get("token", ""))

    @token.setter
    def token(self, v: str):
        self._data["token"] = v

    @property
    def ssl_verify(self) -> bool:
        """Whether to verify SSL certificates. False for self-signed certs."""
        env = os.environ.get("PORTAINER_SSL_VERIFY")
        if env is not None:
            return env.lower() not in ("0", "false", "no")
        return self._data.get("ssl_verify", True)

    @ssl_verify.setter
    def ssl_verify(self, v: bool):
        self._data["ssl_verify"] = v

    def api_base(self) -> str:
        if not self.url:
            raise ConfigError("Portainer URL not configured. Run: cli-anything-portainer config set --url <url>")
        return f"{self.url}/api"

    def auth_headers(self) -> dict:
        if not self.token:
            raise ConfigError(
                "Not logged in. Run: cli-anything-portainer login\n"
                "Or set PORTAINER_TOKEN env var."
            )
        hdrs = {"Content-Type": "application/json"}
        if self.token.startswith("ptr_"):
            # Portainer API key
            hdrs["X-API-Key"] = self.token
        else:
            # JWT from login
            hdrs["Authorization"] = f"Bearer {self.token}"
        return hdrs

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "username": self.username,
            "token": "***" if self.token else "",
            "ssl_verify": self.ssl_verify,
            "config_path": str(self.config_path),
        }
