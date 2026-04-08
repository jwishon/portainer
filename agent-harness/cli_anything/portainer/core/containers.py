"""Container operations via Portainer's Docker proxy."""

from cli_anything.portainer.core.session import PortainerSession


class ContainerClient:
    """Wraps Docker API calls proxied through Portainer at /api/endpoints/{id}/docker/..."""

    def __init__(self, session: PortainerSession, env_id: int):
        self.session = session
        self.env_id = env_id

    def _docker(self, path: str) -> str:
        return f"endpoints/{self.env_id}/docker/{path.lstrip('/')}"

    def list(self, all: bool = False) -> list:
        """GET /containers/json"""
        params = {"all": "1" if all else "0"}
        return self.session.get(self._docker("containers/json"), params=params) or []

    def inspect(self, container_id: str) -> dict:
        """GET /containers/{id}/json"""
        return self.session.get(self._docker(f"containers/{container_id}/json"))

    def start(self, container_id: str) -> None:
        """POST /containers/{id}/start"""
        self.session.post(self._docker(f"containers/{container_id}/start"))

    def stop(self, container_id: str, timeout: int = 10) -> None:
        """POST /containers/{id}/stop"""
        self.session.post(self._docker(f"containers/{container_id}/stop"),
                          params={"t": timeout})

    def restart(self, container_id: str, timeout: int = 10) -> None:
        """POST /containers/{id}/restart"""
        self.session.post(self._docker(f"containers/{container_id}/restart"),
                          params={"t": timeout})

    def kill(self, container_id: str, signal: str = "SIGKILL") -> None:
        """POST /containers/{id}/kill"""
        self.session.post(self._docker(f"containers/{container_id}/kill"),
                          params={"signal": signal})

    def remove(self, container_id: str, force: bool = False, volumes: bool = False) -> None:
        """DELETE /containers/{id}"""
        self.session.delete(self._docker(f"containers/{container_id}"),
                            params={"force": str(force).lower(), "v": str(volumes).lower()})

    def logs(self, container_id: str, tail: int = 100,
             stdout: bool = True, stderr: bool = True) -> str:
        """GET /containers/{id}/logs"""
        params = {
            "stdout": "1" if stdout else "0",
            "stderr": "1" if stderr else "0",
            "tail": str(tail),
        }
        result = self.session.get(self._docker(f"containers/{container_id}/logs"), params=params)
        return str(result or "")

    def stats(self, container_id: str) -> dict:
        """GET /containers/{id}/stats?stream=false"""
        return self.session.get(self._docker(f"containers/{container_id}/stats"),
                                params={"stream": "false"})

    def top(self, container_id: str) -> dict:
        """GET /containers/{id}/top"""
        return self.session.get(self._docker(f"containers/{container_id}/top"))

    def recreate(self, container_id: str, pull_image: bool = True) -> dict:
        """POST /api/docker/{id}/containers/{containerId}/recreate"""
        return self.session.post(
            f"docker/{self.env_id}/containers/{container_id}/recreate",
            json={"PullImage": pull_image},
        )
