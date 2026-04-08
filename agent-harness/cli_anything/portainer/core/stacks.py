"""Stack operations for Portainer API."""

from cli_anything.portainer.core.session import PortainerSession


class StackClient:
    def __init__(self, session: PortainerSession):
        self.session = session

    def list(self, env_id: int = None) -> list:
        """GET /api/stacks"""
        params = {}
        if env_id is not None:
            params["filters"] = f'{{"EndpointID":{env_id}}}'
        result = self.session.get("stacks", params=params or None)
        return result if isinstance(result, list) else []

    def get(self, stack_id: int) -> dict:
        """GET /api/stacks/{id}"""
        return self.session.get(f"stacks/{stack_id}")

    def get_file(self, stack_id: int) -> str:
        """GET /api/stacks/{id}/file — returns compose file content."""
        data = self.session.get(f"stacks/{stack_id}/file")
        if isinstance(data, dict):
            return data.get("StackFileContent", "")
        return str(data or "")

    def create_compose(self, name: str, env_id: int, compose_content: str,
                       env_vars: list[dict] = None) -> dict:
        """POST /api/stacks/create/standalone/string?endpointId={id}

        Creates a Compose stack from a string.
        env_vars: [{"name": "KEY", "value": "VAL"}, ...]
        """
        payload = {
            "name": name,
            "stackFileContent": compose_content,
            "env": env_vars or [],
        }
        return self.session.post(
            "stacks/create/standalone/string",
            json=payload,
            params={"endpointId": env_id},
        )

    def create_from_git(self, name: str, env_id: int, repo_url: str,
                        compose_path: str = "docker-compose.yml",
                        branch: str = "main",
                        env_vars: list[dict] = None) -> dict:
        """POST /api/stacks/create/standalone/repository"""
        payload = {
            "name": name,
            "repositoryURL": repo_url,
            "composeFile": compose_path,
            "repositoryReferenceName": f"refs/heads/{branch}",
            "env": env_vars or [],
        }
        return self.session.post(
            "stacks/create/standalone/repository",
            json=payload,
            params={"endpointId": env_id},
        )

    def update(self, stack_id: int, compose_content: str = None,
               env_vars: list[dict] = None, prune: bool = False) -> dict:
        """PUT /api/stacks/{id}"""
        payload: dict = {"prune": prune, "pullImage": False}
        if compose_content is not None:
            payload["stackFileContent"] = compose_content
        if env_vars is not None:
            payload["env"] = env_vars
        return self.session.put(f"stacks/{stack_id}", json=payload)

    def delete(self, stack_id: int, env_id: int) -> None:
        """DELETE /api/stacks/{id}?endpointId={endpointId}"""
        self.session.delete(f"stacks/{stack_id}", params={"endpointId": env_id})

    def start(self, stack_id: int) -> dict:
        """POST /api/stacks/{id}/start"""
        return self.session.post(f"stacks/{stack_id}/start")

    def stop(self, stack_id: int) -> dict:
        """POST /api/stacks/{id}/stop"""
        return self.session.post(f"stacks/{stack_id}/stop")

    def redeploy(self, stack_id: int, env_id: int, pull_image: bool = True) -> dict:
        """PUT /api/stacks/{id}/git/redeploy"""
        payload = {"endpointId": env_id, "pullImage": pull_image}
        return self.session.put(f"stacks/{stack_id}/git/redeploy", json=payload)
