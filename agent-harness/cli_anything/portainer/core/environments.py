"""Environment (endpoint) operations for Portainer API."""

from cli_anything.portainer.core.session import PortainerSession


class EnvironmentClient:
    def __init__(self, session: PortainerSession):
        self.session = session

    def list(self) -> list:
        """GET /api/endpoints"""
        result = self.session.get("endpoints")
        if isinstance(result, list):
            return result
        # Portainer may return {"totalCount": N, "value": [...]}
        if isinstance(result, dict):
            return result.get("value", [])
        return []

    def get(self, env_id: int) -> dict:
        """GET /api/endpoints/{id}"""
        return self.session.get(f"endpoints/{env_id}")

    def create(self, name: str, url: str, env_type: int = 1, public_url: str = "") -> dict:
        """POST /api/endpoints (admin only).
        env_type: 1=Docker, 2=Agent, 3=Azure
        """
        payload = {
            "Name": name,
            "URL": url,
            "EndpointCreationType": env_type,
        }
        if public_url:
            payload["PublicURL"] = public_url
        return self.session.post("endpoints", json=payload)

    def update(self, env_id: int, **kwargs) -> dict:
        """PUT /api/endpoints/{id}"""
        payload = {k: v for k, v in kwargs.items() if v is not None}
        return self.session.put(f"endpoints/{env_id}", json=payload)

    def delete(self, env_id: int) -> None:
        """DELETE /api/endpoints/{id}"""
        self.session.delete(f"endpoints/{env_id}")

    def snapshot(self, env_id: int) -> None:
        """POST /api/endpoints/{id}/snapshot"""
        self.session.post(f"endpoints/{env_id}/snapshot")

    def list_registries(self, env_id: int) -> list:
        """GET /api/endpoints/{id}/registries"""
        return self.session.get(f"endpoints/{env_id}/registries") or []
