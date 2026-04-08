"""Volume operations via Portainer's Docker proxy."""

from cli_anything.portainer.core.session import PortainerSession


class VolumeClient:
    def __init__(self, session: PortainerSession, env_id: int):
        self.session = session
        self.env_id = env_id

    def _docker(self, path: str) -> str:
        return f"endpoints/{self.env_id}/docker/{path.lstrip('/')}"

    def list(self) -> list:
        """GET /volumes"""
        data = self.session.get(self._docker("volumes"))
        if isinstance(data, dict):
            return data.get("Volumes", []) or []
        return data or []

    def inspect(self, name: str) -> dict:
        """GET /volumes/{name}"""
        return self.session.get(self._docker(f"volumes/{name}"))

    def create(self, name: str, driver: str = "local", labels: dict = None) -> dict:
        """POST /volumes/create"""
        payload: dict = {"Name": name, "Driver": driver}
        if labels:
            payload["Labels"] = labels
        return self.session.post(self._docker("volumes/create"), json=payload)

    def remove(self, name: str, force: bool = False) -> None:
        """DELETE /volumes/{name}"""
        self.session.delete(self._docker(f"volumes/{name}"),
                            params={"force": str(force).lower()})

    def prune(self) -> dict:
        """POST /volumes/prune"""
        return self.session.post(self._docker("volumes/prune"))
