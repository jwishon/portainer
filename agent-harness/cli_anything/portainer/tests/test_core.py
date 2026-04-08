"""Unit tests for cli-anything-portainer core clients."""

import pytest
from unittest.mock import MagicMock, patch

from cli_anything.portainer.utils.config import Config, ConfigError
from cli_anything.portainer.utils.output import OutputFormatter
from cli_anything.portainer.core.session import PortainerSession, APIError
from cli_anything.portainer.core.environments import EnvironmentClient
from cli_anything.portainer.core.stacks import StackClient
from cli_anything.portainer.core.containers import ContainerClient
from cli_anything.portainer.core.images import ImageClient
from cli_anything.portainer.core.volumes import VolumeClient
from cli_anything.portainer.core.networks import NetworkClient
from cli_anything.portainer.core.users import UserClient
from cli_anything.portainer.core.teams import TeamClient
from cli_anything.portainer.core.registries import RegistryClient


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_defaults_empty(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        assert cfg.url == ""
        assert cfg.token == ""

    def test_set_and_save(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.url = "http://portainer.example.com"
        cfg.token = "jwt123"
        cfg.save()

        cfg2 = Config(config_path=tmp_path / "cfg.json")
        assert cfg2.url == "http://portainer.example.com"
        assert cfg2.token == "jwt123"

    def test_url_strips_trailing_slash(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.url = "http://portainer.example.com/"
        assert cfg.url == "http://portainer.example.com"

    def test_api_base(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.url = "http://portainer.example.com"
        assert cfg.api_base() == "http://portainer.example.com/api"

    def test_api_base_raises_without_url(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        with pytest.raises(ConfigError):
            cfg.api_base()

    def test_auth_headers_raises_without_token(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.url = "http://portainer.example.com"
        with pytest.raises(ConfigError):
            cfg.auth_headers()

    def test_auth_headers_bearer(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.url = "http://portainer.example.com"
        cfg.token = "myjwt"
        hdrs = cfg.auth_headers()
        assert hdrs["Authorization"] == "Bearer myjwt"

    def test_env_var_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PORTAINER_URL", "http://override.example.com")
        monkeypatch.setenv("PORTAINER_TOKEN", "env_token")
        cfg = Config(config_path=tmp_path / "cfg.json")
        assert cfg.url == "http://override.example.com"
        assert cfg.token == "env_token"

    def test_to_dict_masks_token(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        cfg.url = "http://portainer.example.com"
        cfg.token = "secret_jwt"
        d = cfg.to_dict()
        assert d["token"] == "***"

    def test_to_dict_empty_token(self, tmp_path):
        cfg = Config(config_path=tmp_path / "cfg.json")
        d = cfg.to_dict()
        assert d["token"] == ""


# ---------------------------------------------------------------------------
# OutputFormatter
# ---------------------------------------------------------------------------

class TestOutputFormatter:
    def test_success_json(self):
        fmt = OutputFormatter(json_mode=True)
        import json
        result = json.loads(fmt.success({"key": "value"}))
        assert result["success"] is True
        assert result["data"]["key"] == "value"

    def test_error_json(self):
        fmt = OutputFormatter(json_mode=True)
        import json
        result = json.loads(fmt.error("something broke"))
        assert result["success"] is False
        assert "something broke" in result["error"]

    def test_success_human_dict(self):
        fmt = OutputFormatter(json_mode=False)
        result = fmt.success({"Name": "test"})
        assert "Name" in result
        assert "test" in result

    def test_success_human_list(self):
        fmt = OutputFormatter(json_mode=False)
        result = fmt.success([{"Name": "a"}, {"Name": "b"}])
        assert "a" in result
        assert "b" in result

    def test_error_human(self):
        fmt = OutputFormatter(json_mode=False)
        result = fmt.error("oops")
        assert "oops" in result


# ---------------------------------------------------------------------------
# APIError
# ---------------------------------------------------------------------------

class TestAPIError:
    def test_message_and_status(self):
        e = APIError("not found", status_code=404)
        assert "not found" in str(e)
        assert e.status_code == 404


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def _make_session(tmp_path, token="test_jwt"):
    cfg = Config(config_path=tmp_path / "cfg.json")
    cfg.url = "http://portainer.example.com"
    cfg.token = token
    return PortainerSession(config=cfg)


class TestPortainerSession:
    def test_url_construction(self, tmp_path):
        s = _make_session(tmp_path)
        assert s._url("endpoints") == "http://portainer.example.com/api/endpoints"

    def test_url_strips_leading_slash(self, tmp_path):
        s = _make_session(tmp_path)
        assert s._url("/endpoints") == "http://portainer.example.com/api/endpoints"

    def test_raise_on_4xx(self, tmp_path):
        s = _make_session(tmp_path)
        resp = MagicMock()
        resp.status_code = 404
        resp.json.return_value = {"message": "not found"}
        with pytest.raises(APIError) as exc_info:
            s._raise(resp)
        assert exc_info.value.status_code == 404

    def test_no_raise_on_2xx(self, tmp_path):
        s = _make_session(tmp_path)
        resp = MagicMock()
        resp.status_code = 200
        s._raise(resp)  # should not raise


# ---------------------------------------------------------------------------
# EnvironmentClient
# ---------------------------------------------------------------------------

class TestEnvironmentClient:
    def _client(self, tmp_path):
        return EnvironmentClient(_make_session(tmp_path))

    def test_list_returns_list(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value=[{"Id": 1, "Name": "local"}])
        result = client.list()
        assert isinstance(result, list)
        assert result[0]["Id"] == 1

    def test_list_handles_dict_response(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value={"value": [{"Id": 2}], "totalCount": 1})
        result = client.list()
        assert result[0]["Id"] == 2

    def test_list_handles_none(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value=None)
        assert client.list() == []

    def test_get(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value={"Id": 1})
        assert client.get(1)["Id"] == 1
        client.session.get.assert_called_with("endpoints/1")

    def test_snapshot(self, tmp_path):
        client = self._client(tmp_path)
        client.session.post = MagicMock(return_value=None)
        client.snapshot(1)
        client.session.post.assert_called_with("endpoints/1/snapshot")


# ---------------------------------------------------------------------------
# StackClient
# ---------------------------------------------------------------------------

class TestStackClient:
    def _client(self, tmp_path):
        return StackClient(_make_session(tmp_path))

    def test_list_no_filter(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value=[{"Id": 1}])
        result = client.list()
        assert len(result) == 1
        client.session.get.assert_called_with("stacks", params=None)

    def test_list_with_env_filter(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value=[{"Id": 2}])
        client.list(env_id=3)
        call_kwargs = client.session.get.call_args
        assert call_kwargs[1]["params"]["filters"] is not None

    def test_get(self, tmp_path):
        client = self._client(tmp_path)
        client.session.get = MagicMock(return_value={"Id": 5})
        assert client.get(5)["Id"] == 5

    def test_delete_with_env_id(self, tmp_path):
        client = self._client(tmp_path)
        client.session.delete = MagicMock(return_value=None)
        client.delete(5, env_id=2)
        client.session.delete.assert_called_with("stacks/5", params={"endpointId": 2})

    def test_delete_requires_env_id(self, tmp_path):
        client = self._client(tmp_path)
        with pytest.raises(TypeError):
            client.delete(5)  # env_id is required positional arg


# ---------------------------------------------------------------------------
# ContainerClient
# ---------------------------------------------------------------------------

class TestContainerClient:
    def _client(self, tmp_path):
        return ContainerClient(_make_session(tmp_path), env_id=1)

    def test_docker_path(self, tmp_path):
        c = self._client(tmp_path)
        assert c._docker("containers/json") == "endpoints/1/docker/containers/json"

    def test_list_all_false(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[])
        c.list(all=False)
        c.session.get.assert_called_with("endpoints/1/docker/containers/json", params={"all": "0"})

    def test_list_all_true(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[])
        c.list(all=True)
        c.session.get.assert_called_with("endpoints/1/docker/containers/json", params={"all": "1"})

    def test_inspect(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value={"Id": "abc"})
        result = c.inspect("abc")
        assert result["Id"] == "abc"

    def test_start(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value=None)
        c.start("abc")
        c.session.post.assert_called_with("endpoints/1/docker/containers/abc/start")

    def test_stop(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value=None)
        c.stop("abc", timeout=5)
        c.session.post.assert_called_with("endpoints/1/docker/containers/abc/stop",
                                          params={"t": 5})

    def test_remove(self, tmp_path):
        c = self._client(tmp_path)
        c.session.delete = MagicMock(return_value=None)
        c.remove("abc", force=True)
        c.session.delete.assert_called_with("endpoints/1/docker/containers/abc",
                                             params={"force": "true", "v": "false"})

    def test_logs_returns_str(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value="log line\n")
        result = c.logs("abc", tail=10)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# ImageClient
# ---------------------------------------------------------------------------

class TestImageClient:
    def _client(self, tmp_path):
        return ImageClient(_make_session(tmp_path), env_id=2)

    def test_list(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"Id": "sha256:abc"}])
        result = c.list()
        assert len(result) == 1

    def test_pull(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={})
        c.pull("nginx", tag="latest")
        c.session.post.assert_called_with(
            "endpoints/2/docker/images/create",
            params={"fromImage": "nginx", "tag": "latest"},
        )

    def test_remove(self, tmp_path):
        c = self._client(tmp_path)
        c.session.delete = MagicMock(return_value=[])
        c.remove("nginx:latest", force=True)
        c.session.delete.assert_called_with("endpoints/2/docker/images/nginx:latest",
                                             params={"force": "true"})

    def test_prune(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"ImagesDeleted": []})
        result = c.prune()
        assert "ImagesDeleted" in result


# ---------------------------------------------------------------------------
# VolumeClient
# ---------------------------------------------------------------------------

class TestVolumeClient:
    def _client(self, tmp_path):
        return VolumeClient(_make_session(tmp_path), env_id=1)

    def test_list_from_dict(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value={"Volumes": [{"Name": "vol1"}], "Warnings": None})
        result = c.list()
        assert result[0]["Name"] == "vol1"

    def test_list_from_list(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"Name": "vol2"}])
        result = c.list()
        assert result[0]["Name"] == "vol2"

    def test_create(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Name": "myvol"})
        result = c.create("myvol", driver="local")
        c.session.post.assert_called_with(
            "endpoints/1/docker/volumes/create",
            json={"Name": "myvol", "Driver": "local"},
        )

    def test_remove(self, tmp_path):
        c = self._client(tmp_path)
        c.session.delete = MagicMock(return_value=None)
        c.remove("myvol", force=True)
        c.session.delete.assert_called_with("endpoints/1/docker/volumes/myvol",
                                             params={"force": "true"})


# ---------------------------------------------------------------------------
# NetworkClient
# ---------------------------------------------------------------------------

class TestNetworkClient:
    def _client(self, tmp_path):
        return NetworkClient(_make_session(tmp_path), env_id=1)

    def test_list(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"Id": "net1"}])
        result = c.list()
        assert result[0]["Id"] == "net1"

    def test_create_with_labels(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Id": "newnet"})
        c.create("mynet", driver="bridge", labels={"app": "test"})
        call_kwargs = c.session.post.call_args
        assert call_kwargs[1]["json"]["Labels"] == {"app": "test"}

    def test_prune(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"NetworksDeleted": []})
        result = c.prune()
        c.session.post.assert_called_with("endpoints/1/docker/networks/prune")


# ---------------------------------------------------------------------------
# UserClient
# ---------------------------------------------------------------------------

class TestUserClient:
    def _client(self, tmp_path):
        return UserClient(_make_session(tmp_path))

    def test_list(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"Id": 1, "Username": "admin"}])
        result = c.list()
        assert result[0]["Username"] == "admin"

    def test_me(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value={"Id": 1, "Username": "admin"})
        result = c.me()
        c.session.get.assert_called_with("users/me")

    def test_create(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Id": 2})
        c.create("newuser", "pass123", role=2)
        c.session.post.assert_called_with(
            "users",
            json={"username": "newuser", "password": "pass123", "role": 2},
        )

    def test_delete(self, tmp_path):
        c = self._client(tmp_path)
        c.session.delete = MagicMock(return_value=None)
        c.delete(3)
        c.session.delete.assert_called_with("users/3")

    def test_change_password(self, tmp_path):
        c = self._client(tmp_path)
        c.session.put = MagicMock(return_value=None)
        c.change_password(1, "old", "new")
        c.session.put.assert_called_with(
            "users/1/passwd",
            json={"password": "old", "newPassword": "new"},
        )

    def test_create_api_key(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"rawAPIKey": "key123"})
        result = c.create_api_key(1, "my key")
        c.session.post.assert_called_with("users/1/tokens", json={"description": "my key"})


# ---------------------------------------------------------------------------
# TeamClient
# ---------------------------------------------------------------------------

class TestTeamClient:
    def _client(self, tmp_path):
        return TeamClient(_make_session(tmp_path))

    def test_list(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"Id": 1, "Name": "devs"}])
        result = c.list()
        assert result[0]["Name"] == "devs"

    def test_create(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Id": 2, "Name": "ops"})
        c.create("ops")
        c.session.post.assert_called_with("teams", json={"name": "ops"})

    def test_delete(self, tmp_path):
        c = self._client(tmp_path)
        c.session.delete = MagicMock(return_value=None)
        c.delete(1)
        c.session.delete.assert_called_with("teams/1")

    def test_add_member(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Id": 1})
        c.add_member(team_id=1, user_id=5, role=2)
        c.session.post.assert_called_with(
            "teams/1/memberships",
            json={"userID": 5, "role": 2},
        )

    def test_list_memberships(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"UserId": 1}])
        result = c.list_memberships(1)
        c.session.get.assert_called_with("teams/1/memberships")


# ---------------------------------------------------------------------------
# RegistryClient
# ---------------------------------------------------------------------------

class TestRegistryClient:
    def _client(self, tmp_path):
        return RegistryClient(_make_session(tmp_path))

    def test_list(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value=[{"Id": 1, "Name": "dockerhub"}])
        result = c.list()
        assert result[0]["Name"] == "dockerhub"

    def test_create_no_auth(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Id": 1})
        c.create("myreg", "https://registry.example.com", registry_type=1)
        call_json = c.session.post.call_args[1]["json"]
        assert call_json["name"] == "myreg"
        assert "authentication" not in call_json

    def test_create_with_auth(self, tmp_path):
        c = self._client(tmp_path)
        c.session.post = MagicMock(return_value={"Id": 1})
        c.create("myreg", "https://registry.example.com", username="user", password="pass")
        call_json = c.session.post.call_args[1]["json"]
        assert call_json["authentication"] is True
        assert call_json["username"] == "user"

    def test_delete(self, tmp_path):
        c = self._client(tmp_path)
        c.session.delete = MagicMock(return_value=None)
        c.delete(1)
        c.session.delete.assert_called_with("registries/1")

    def test_list_repositories_from_dict(self, tmp_path):
        c = self._client(tmp_path)
        c.session.get = MagicMock(return_value={"repositories": ["repo1", "repo2"]})
        result = c.list_repositories(1)
        assert "repo1" in result
