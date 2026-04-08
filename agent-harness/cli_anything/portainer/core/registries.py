"""Registry management for Portainer API."""

from cli_anything.portainer.core.session import PortainerSession


class RegistryClient:
    def __init__(self, session: PortainerSession):
        self.session = session

    def list(self) -> list:
        return self.session.get("registries") or []

    def get(self, registry_id: int) -> dict:
        return self.session.get(f"registries/{registry_id}")

    def create(self, name: str, url: str, registry_type: int = 1,
               username: str = None, password: str = None) -> dict:
        """
        registry_type: 1=custom, 2=quay.io, 3=azure, 4=gitlab, 5=ProGet, 6=DockerHub, 7=ECR
        """
        payload: dict = {"name": name, "url": url, "type": registry_type}
        if username:
            payload["authentication"] = True
            payload["username"] = username
            payload["password"] = password or ""
        return self.session.post("registries", json=payload)

    def update(self, registry_id: int, **kwargs) -> dict:
        payload = {k: v for k, v in kwargs.items() if v is not None}
        return self.session.put(f"registries/{registry_id}", json=payload)

    def delete(self, registry_id: int) -> None:
        self.session.delete(f"registries/{registry_id}")

    def list_repositories(self, registry_id: int) -> list:
        data = self.session.get(f"registries/{registry_id}/repositories")
        if isinstance(data, dict):
            return data.get("repositories", []) or []
        return data or []

    def delete_repository(self, registry_id: int, repository: str) -> None:
        self.session.delete(f"registries/{registry_id}/repositories/{repository}")
