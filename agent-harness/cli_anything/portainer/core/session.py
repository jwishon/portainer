"""HTTP session for Portainer REST API."""

import urllib3
import requests
from typing import Any
from cli_anything.portainer.utils.config import Config, ConfigError

# Suppress InsecureRequestWarning when ssl_verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class APIError(Exception):
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class PortainerSession:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._session = requests.Session()
        self._verify = self.config.ssl_verify

    def _url(self, path: str) -> str:
        return f"{self.config.api_base()}/{path.lstrip('/')}"

    def _hdrs(self) -> dict:
        return self.config.auth_headers()

    def _raise(self, resp: requests.Response):
        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("message") or body.get("err") or body.get("details") or resp.text
            except Exception:
                msg = resp.text or f"HTTP {resp.status_code}"
            raise APIError(str(msg), status_code=resp.status_code)

    def get(self, path: str, params: dict = None) -> Any:
        resp = self._session.get(self._url(path), headers=self._hdrs(), params=params,
                                 timeout=30, verify=self._verify)
        self._raise(resp)
        if not resp.content:
            return None
        return resp.json()

    def post(self, path: str, json: dict = None, params: dict = None, auth: bool = True) -> Any:
        headers = self._hdrs() if auth else {"Content-Type": "application/json"}
        resp = self._session.post(self._url(path), headers=headers, json=json or {},
                                  params=params, timeout=30, verify=self._verify)
        self._raise(resp)
        if not resp.content:
            return None
        try:
            return resp.json()
        except Exception:
            return resp.text

    def put(self, path: str, json: dict = None, params: dict = None) -> Any:
        resp = self._session.put(self._url(path), headers=self._hdrs(), json=json or {},
                                 params=params, timeout=30, verify=self._verify)
        self._raise(resp)
        if not resp.content:
            return None
        try:
            return resp.json()
        except Exception:
            return resp.text

    def delete(self, path: str, params: dict = None) -> None:
        resp = self._session.delete(self._url(path), headers=self._hdrs(), params=params,
                                    timeout=30, verify=self._verify)
        self._raise(resp)
