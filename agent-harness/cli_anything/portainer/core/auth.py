"""Authentication for Portainer API."""

import requests
from cli_anything.portainer.utils.config import Config, ConfigError
from cli_anything.portainer.core.session import APIError


def login(config: Config, username: str = None, password: str = None) -> str:
    """POST /api/auth — returns JWT token and saves to config."""
    url = config.url
    if not url:
        raise ConfigError("URL not configured. Run: cli-anything-portainer config set --url <url>")
    u = username or config.username
    p = password or config.password
    if not u or not p:
        raise ConfigError("Username and password required. Run: cli-anything-portainer login")
    resp = requests.post(
        f"{url}/api/auth",
        json={"username": u, "password": p},
        headers={"Content-Type": "application/json"},
        timeout=30,
        verify=config.ssl_verify,
    )
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("message", resp.text)
        except Exception:
            msg = resp.text
        raise APIError(str(msg), status_code=resp.status_code)
    token = resp.json().get("jwt", "")
    config.token = token
    config.save()
    return token


def logout(config: Config) -> None:
    """POST /api/auth/logout — invalidates current token."""
    if not config.token:
        return
    requests.post(
        f"{config.url}/api/auth/logout",
        headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"},
        timeout=10,
    )
    config.token = ""
    config.save()
