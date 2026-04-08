"""Network operations via Portainer's Docker proxy."""

from cli_anything.portainer.core.session import PortainerSession


class NetworkClient:
    def __init__(self, session: PortainerSession, env_id: int):
        self.session = session
        self.env_id = env_id

    def _docker(self, path: str) -> str:
        return f"endpoints/{self.env_id}/docker/{path.lstrip('/')}"

    def list(self) -> list:
        return self.session.get(self._docker("networks")) or []

    def inspect(self, network_id: str) -> dict:
        return self.session.get(self._docker(f"networks/{network_id}"))

    def create(self, name: str, driver: str = "bridge", labels: dict = None) -> dict:
        payload: dict = {"Name": name, "Driver": driver}
        if labels:
            payload["Labels"] = labels
        return self.session.post(self._docker("networks/create"), json=payload)

    def remove(self, network_id: str) -> None:
        self.session.delete(self._docker(f"networks/{network_id}"))

    def prune(self) -> dict:
        return self.session.post(self._docker("networks/prune"))
