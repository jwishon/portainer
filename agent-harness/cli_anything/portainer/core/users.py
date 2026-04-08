"""User management for Portainer API."""

from cli_anything.portainer.core.session import PortainerSession


class UserClient:
    def __init__(self, session: PortainerSession):
        self.session = session

    def list(self) -> list:
        return self.session.get("users") or []

    def me(self) -> dict:
        return self.session.get("users/me")

    def get(self, user_id: int) -> dict:
        return self.session.get(f"users/{user_id}")

    def create(self, username: str, password: str, role: int = 2) -> dict:
        """role: 1=admin, 2=regular"""
        return self.session.post("users", json={"username": username, "password": password, "role": role})

    def update(self, user_id: int, **kwargs) -> dict:
        payload = {k: v for k, v in kwargs.items() if v is not None}
        return self.session.put(f"users/{user_id}", json=payload)

    def delete(self, user_id: int) -> None:
        self.session.delete(f"users/{user_id}")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        self.session.put(f"users/{user_id}/passwd",
                         json={"password": old_password, "newPassword": new_password})

    def list_memberships(self, user_id: int) -> list:
        return self.session.get(f"users/{user_id}/memberships") or []

    def create_api_key(self, user_id: int, description: str) -> dict:
        return self.session.post(f"users/{user_id}/tokens", json={"description": description})

    def list_api_keys(self, user_id: int) -> list:
        return self.session.get(f"users/{user_id}/tokens") or []
