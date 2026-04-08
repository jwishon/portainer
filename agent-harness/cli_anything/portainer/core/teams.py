"""Team management for Portainer API."""

from cli_anything.portainer.core.session import PortainerSession


class TeamClient:
    def __init__(self, session: PortainerSession):
        self.session = session

    def list(self) -> list:
        return self.session.get("teams") or []

    def get(self, team_id: int) -> dict:
        return self.session.get(f"teams/{team_id}")

    def create(self, name: str) -> dict:
        return self.session.post("teams", json={"name": name})

    def update(self, team_id: int, name: str) -> dict:
        return self.session.put(f"teams/{team_id}", json={"name": name})

    def delete(self, team_id: int) -> None:
        self.session.delete(f"teams/{team_id}")

    def list_memberships(self, team_id: int) -> list:
        return self.session.get(f"teams/{team_id}/memberships") or []

    def add_member(self, team_id: int, user_id: int, role: int = 2) -> dict:
        """role: 1=leader, 2=member"""
        return self.session.post(f"teams/{team_id}/memberships",
                                 json={"userID": user_id, "role": role})

    def update_member(self, team_id: int, membership_id: int, role: int) -> dict:
        return self.session.put(f"team_memberships/{membership_id}", json={"role": role})

    def remove_member(self, team_id: int, membership_id: int) -> None:
        self.session.delete(f"team_memberships/{membership_id}")
