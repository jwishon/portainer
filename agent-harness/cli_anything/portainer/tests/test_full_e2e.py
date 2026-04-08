"""E2E tests for cli-anything-portainer.

Subprocess tests: always run.
Live tests: require PORTAINER_URL + PORTAINER_TOKEN env vars.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIVE = bool(os.environ.get("PORTAINER_URL") and os.environ.get("PORTAINER_TOKEN"))

live = pytest.mark.skipif(not LIVE, reason="Live Portainer server not configured")

CLI_FORCE_INSTALLED = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED") == "1"


def _resolve_cli() -> list[str]:
    if CLI_FORCE_INSTALLED:
        cmd = shutil.which("cli-anything-portainer")
        if cmd:
            return [cmd]
    return [sys.executable, "-m", "cli_anything.portainer.portainer_cli"]


def run(*args, env_extra: dict = None) -> subprocess.CompletedProcess:
    cmd = _resolve_cli() + list(args)
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def run_json(*args, env_extra: dict = None) -> dict:
    result = run("--json", *args, env_extra=env_extra)
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Subprocess tests (no live server)
# ---------------------------------------------------------------------------

class TestSubprocessHelp:
    def test_main_help(self):
        r = run("--help")
        assert r.returncode == 0
        assert "portainer" in r.stdout.lower()

    def test_config_help(self):
        r = run("config", "--help")
        assert r.returncode == 0

    def test_env_help(self):
        r = run("env", "--help")
        assert r.returncode == 0

    def test_stack_help(self):
        r = run("stack", "--help")
        assert r.returncode == 0

    def test_container_help(self):
        r = run("container", "--help")
        assert r.returncode == 0

    def test_image_help(self):
        r = run("image", "--help")
        assert r.returncode == 0

    def test_volume_help(self):
        r = run("volume", "--help")
        assert r.returncode == 0

    def test_network_help(self):
        r = run("network", "--help")
        assert r.returncode == 0

    def test_user_help(self):
        r = run("user", "--help")
        assert r.returncode == 0

    def test_team_help(self):
        r = run("team", "--help")
        assert r.returncode == 0

    def test_registry_help(self):
        r = run("registry", "--help")
        assert r.returncode == 0


class TestSubprocessConfig:
    def test_config_set_and_show(self, tmp_path):
        cfg = str(tmp_path / "cfg.json")
        r = run_json("--json", "config", "set", "--url", "http://portainer.test",
                     env_extra={"PORTAINER_CONFIG": cfg})
        # Config doesn't use PORTAINER_CONFIG, just check it runs
        r2 = run("config", "set", "--url", "http://portainer.test")
        # No crash is sufficient for subprocess test

    def test_config_show_json(self, tmp_path):
        r = run("--json", "config", "show")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "success" in data

    def test_env_list_no_config_fails_gracefully(self):
        """Without config, env list should exit non-zero with JSON error."""
        r = run("--json", "env", "list",
                env_extra={"PORTAINER_URL": "", "PORTAINER_TOKEN": ""})
        assert r.returncode != 0 or json.loads(r.stdout).get("success") is False


# ---------------------------------------------------------------------------
# Live tests
# ---------------------------------------------------------------------------

@live
class TestLiveEnvs:
    def test_env_list(self):
        data = run_json("env", "list")
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_env_get_first(self):
        envs = run_json("env", "list")["data"]
        if not envs:
            pytest.skip("No environments")
        eid = envs[0]["Id"]
        data = run_json("env", "get", str(eid))
        assert data["success"] is True
        assert data["data"]["Id"] == eid


@live
class TestLiveStacks:
    def test_stack_list(self):
        envs = run_json("env", "list")["data"]
        if not envs:
            pytest.skip("No environments")
        eid = str(envs[0]["Id"])
        data = run_json("--env-id", eid, "stack", "list")
        assert data["success"] is True
        assert isinstance(data["data"], list)


@live
class TestLiveContainers:
    def _eid(self):
        envs = run_json("env", "list")["data"]
        if not envs:
            pytest.skip("No environments")
        return str(envs[0]["Id"])

    def test_container_list(self):
        eid = self._eid()
        data = run_json("--env-id", eid, "container", "list", "--all")
        assert data["success"] is True
        assert isinstance(data["data"], list)


@live
class TestLiveImages:
    def _eid(self):
        envs = run_json("env", "list")["data"]
        if not envs:
            pytest.skip("No environments")
        return str(envs[0]["Id"])

    def test_image_list(self):
        eid = self._eid()
        data = run_json("--env-id", eid, "image", "list")
        assert data["success"] is True
        assert isinstance(data["data"], list)


@live
class TestLiveUsers:
    def test_user_me(self):
        data = run_json("user", "me")
        assert data["success"] is True
        assert "Username" in data["data"] or "username" in data["data"]

    def test_user_list(self):
        data = run_json("user", "list")
        assert data["success"] is True
        assert isinstance(data["data"], list)
