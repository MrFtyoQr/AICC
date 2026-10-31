"""Helpers compartidos por las pruebas de workspaces y aislamiento."""

import uuid

from fastapi.testclient import TestClient

PASSWORD = "una-clave-larga-segura"


class Account:
    """Usuario registrado con sesión iniciada y su workspace personal."""

    def __init__(self, client: TestClient, email: str) -> None:
        self.client = client
        self.email = email
        created = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
        assert created.status_code == 201, created.text
        self.user_id = uuid.UUID(created.json()["id"])
        token = client.post(
            "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
        ).json()["access_token"]
        self.auth = {"Authorization": f"Bearer {token}"}
        self.workspace_id = self.get("/api/v1/workspaces/current").json()["id"]

    def headers(self, workspace_id: str | None = None) -> dict[str, str]:
        return {**self.auth, "X-Workspace-Id": workspace_id or self.workspace_id}

    def get(self, path: str, workspace_id: str | None = None):
        headers = self.headers(workspace_id) if workspace_id else self.auth
        return self.client.get(path, headers=headers)

    def request(self, method: str, path: str, workspace_id: str | None = None, **kwargs):
        return self.client.request(method, path, headers=self.headers(workspace_id), **kwargs)

    def first_project(self) -> dict:
        return self.request("GET", "/api/v1/projects").json()[0]
