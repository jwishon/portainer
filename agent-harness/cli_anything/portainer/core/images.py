"""Image operations via Portainer's Docker proxy."""

from cli_anything.portainer.core.session import PortainerSession


class ImageClient:
    def __init__(self, session: PortainerSession, env_id: int):
        self.session = session
        self.env_id = env_id

    def _docker(self, path: str) -> str:
        return f"endpoints/{self.env_id}/docker/{path.lstrip('/')}"

    def list(self) -> list:
        """GET /images/json"""
        return self.session.get(self._docker("images/json")) or []

    def inspect(self, image: str) -> dict:
        """GET /images/{name}/json"""
        return self.session.get(self._docker(f"images/{image}/json"))

    def pull(self, image: str, tag: str = "latest") -> dict:
        """POST /images/create?fromImage=image&tag=tag"""
        return self.session.post(
            self._docker("images/create"),
            params={"fromImage": image, "tag": tag},
        )

    def remove(self, image: str, force: bool = False) -> list:
        """DELETE /images/{name}"""
        return self.session.delete(self._docker(f"images/{image}"),
                                   params={"force": str(force).lower()})

    def tag(self, image: str, repo: str, tag: str = "latest") -> None:
        """POST /images/{name}/tag"""
        self.session.post(self._docker(f"images/{image}/tag"),
                          params={"repo": repo, "tag": tag})

    def prune(self) -> dict:
        """POST /images/prune — remove dangling images."""
        return self.session.post(self._docker("images/prune"))
