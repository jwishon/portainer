"""CLI entry point for cli-anything-portainer."""

import json
import shlex
import sys

import click

from cli_anything.portainer.utils.config import Config, ConfigError
from cli_anything.portainer.utils.output import OutputFormatter
from cli_anything.portainer.core.session import PortainerSession, APIError
from cli_anything.portainer.core.auth import login as _login, logout as _logout
from cli_anything.portainer.core.environments import EnvironmentClient
from cli_anything.portainer.core.stacks import StackClient
from cli_anything.portainer.core.containers import ContainerClient
from cli_anything.portainer.core.images import ImageClient
from cli_anything.portainer.core.volumes import VolumeClient
from cli_anything.portainer.core.networks import NetworkClient
from cli_anything.portainer.core.users import UserClient
from cli_anything.portainer.core.teams import TeamClient
from cli_anything.portainer.core.registries import RegistryClient

pass_ctx = click.make_pass_decorator(dict, ensure=True)


def _fmt(ctx_obj: dict) -> OutputFormatter:
    return OutputFormatter(json_mode=ctx_obj.get("json", False))


def _cfg(ctx_obj: dict) -> Config:
    return ctx_obj.get("config") or Config()


def _session(ctx_obj: dict) -> PortainerSession:
    return PortainerSession(config=_cfg(ctx_obj))


def _out(ctx_obj: dict, data) -> None:
    click.echo(_fmt(ctx_obj).success(data))


def _err(ctx_obj: dict, msg: str, code: int = None) -> None:
    click.echo(_fmt(ctx_obj).error(msg, code), err=True)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output as JSON envelope.")
@click.option("--env-id", default=None, envvar="PORTAINER_ENV_ID",
              help="Portainer environment (endpoint) ID.")
@click.pass_context
def main(ctx, json_mode, env_id):
    """cli-anything-portainer — manage Portainer via CLI."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_mode
    ctx.obj["config"] = Config()
    if env_id:
        ctx.obj["env_id"] = int(env_id)


# ---------------------------------------------------------------------------
# login / logout
# ---------------------------------------------------------------------------

@main.command()
@click.option("--username", "-u", default=None)
@click.option("--password", "-p", default=None, hide_input=True)
@pass_ctx
def login(ctx, username, password):
    """Authenticate and store JWT token."""
    cfg = _cfg(ctx)
    try:
        if not username:
            username = click.prompt("Username")
        if not password:
            password = click.prompt("Password", hide_input=True)
        token = _login(cfg, username=username, password=password)
        _out(ctx, {"token": "***", "message": "Login successful"})
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@main.command()
@pass_ctx
def logout(ctx):
    """Invalidate current JWT token."""
    cfg = _cfg(ctx)
    try:
        _logout(cfg)
        _out(ctx, {"message": "Logged out"})
    except Exception as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# config group
# ---------------------------------------------------------------------------

@main.group()
def config():
    """Manage cli-anything-portainer configuration."""


@config.command("set")
@click.option("--url", default=None)
@click.option("--username", default=None)
@click.option("--password", default=None)
@click.option("--token", default=None)
@click.option("--no-verify", "no_verify", is_flag=True, default=False,
              help="Disable SSL certificate verification (for self-signed certs).")
@pass_ctx
def config_set(ctx, url, username, password, token, no_verify):
    """Set configuration values."""
    cfg = _cfg(ctx)
    if url:
        cfg.url = url
    if username:
        cfg.username = username
    if password:
        cfg.password = password
    if token:
        cfg.token = token
    if no_verify:
        cfg.ssl_verify = False
    cfg.save()
    _out(ctx, cfg.to_dict())


@config.command("show")
@pass_ctx
def config_show(ctx):
    """Show current configuration."""
    cfg = _cfg(ctx)
    _out(ctx, cfg.to_dict())


# ---------------------------------------------------------------------------
# env group
# ---------------------------------------------------------------------------

@main.group()
def env():
    """Manage Portainer environments (endpoints)."""


@env.command("list")
@pass_ctx
def env_list(ctx):
    """List all environments."""
    try:
        client = EnvironmentClient(_session(ctx))
        _out(ctx, client.list())
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@env.command("get")
@click.argument("env_id", type=int)
@pass_ctx
def env_get(ctx, env_id):
    """Get details for an environment."""
    try:
        client = EnvironmentClient(_session(ctx))
        _out(ctx, client.get(env_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@env.command("snapshot")
@click.argument("env_id", type=int)
@pass_ctx
def env_snapshot(ctx, env_id):
    """Trigger a snapshot for an environment."""
    try:
        client = EnvironmentClient(_session(ctx))
        client.snapshot(env_id)
        _out(ctx, {"message": f"Snapshot triggered for environment {env_id}"})
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@env.command("use")
@click.argument("env_id", type=int)
@pass_ctx
def env_use(ctx, env_id):
    """Set default environment ID in config."""
    cfg = _cfg(ctx)
    cfg._data["env_id"] = env_id
    cfg.save()
    ctx.get("env_id", None)
    _out(ctx, {"message": f"Default environment set to {env_id}", "env_id": env_id})


# ---------------------------------------------------------------------------
# stack group
# ---------------------------------------------------------------------------

@main.group()
def stack():
    """Manage Portainer stacks."""


@stack.command("list")
@click.option("--env-id", type=int, default=None)
@pass_ctx
def stack_list(ctx, env_id):
    """List all stacks."""
    eid = env_id or ctx.get("env_id")
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.list(env_id=int(eid) if eid else None))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("get")
@click.argument("stack_id", type=int)
@pass_ctx
def stack_get(ctx, stack_id):
    """Get stack details."""
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.get(stack_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("file")
@click.argument("stack_id", type=int)
@pass_ctx
def stack_file(ctx, stack_id):
    """Get the compose file for a stack."""
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.get_file(stack_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("deploy")
@click.option("--name", required=True)
@click.option("--env-id", type=int, default=None)
@click.option("--file", "compose_file", default=None, help="Path to docker-compose file.")
@click.option("--compose", default=None, help="Compose YAML string.")
@pass_ctx
def stack_deploy(ctx, name, env_id, compose_file, compose):
    """Deploy a new stack from compose content."""
    eid = env_id or ctx.get("env_id")
    if not eid:
        _err(ctx, "--env-id required")
        sys.exit(1)
    content = compose
    if compose_file:
        with open(compose_file) as f:
            content = f.read()
    if not content:
        _err(ctx, "Either --file or --compose required")
        sys.exit(1)
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.create_compose(name=name, compose_content=content, env_id=int(eid)))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("update")
@click.argument("stack_id", type=int)
@click.option("--compose", default=None)
@click.option("--file", "compose_file", default=None)
@click.option("--prune/--no-prune", default=False)
@click.option("--pull/--no-pull", default=True)
@pass_ctx
def stack_update(ctx, stack_id, compose, compose_file, prune, pull):
    """Update an existing stack."""
    content = compose
    if compose_file:
        with open(compose_file) as f:
            content = f.read()
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.update(stack_id, compose_content=content, prune=prune))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("delete")
@click.argument("stack_id", type=int)
@click.option("--env-id", type=int, default=None)
@pass_ctx
def stack_delete(ctx, stack_id, env_id):
    """Delete a stack."""
    eid = env_id or ctx.get("env_id")
    try:
        client = StackClient(_session(ctx))
        if not eid:
            _err(ctx, "--env-id required for stack delete")
            sys.exit(1)
        client.delete(stack_id, env_id=int(eid))
        _out(ctx, {"message": f"Stack {stack_id} deleted"})
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("start")
@click.argument("stack_id", type=int)
@pass_ctx
def stack_start(ctx, stack_id):
    """Start a stopped stack."""
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.start(stack_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("stop")
@click.argument("stack_id", type=int)
@pass_ctx
def stack_stop(ctx, stack_id):
    """Stop a running stack."""
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.stop(stack_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@stack.command("redeploy")
@click.argument("stack_id", type=int)
@click.option("--env-id", type=int, default=None)
@click.option("--pull/--no-pull", default=True)
@pass_ctx
def stack_redeploy(ctx, stack_id, env_id, pull):
    """Redeploy a stack (pull + restart)."""
    eid = env_id or ctx.get("env_id")
    if not eid:
        _err(ctx, "--env-id required for stack redeploy")
        sys.exit(1)
    try:
        client = StackClient(_session(ctx))
        _out(ctx, client.redeploy(stack_id, env_id=int(eid), pull_image=pull))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# container group
# ---------------------------------------------------------------------------

@main.group()
def container():
    """Manage containers via Docker proxy."""


def _container_client(ctx) -> ContainerClient:
    cfg = _cfg(ctx)
    eid = ctx.get("env_id") or cfg._data.get("env_id")
    if not eid:
        raise click.UsageError("--env-id required (or set with: env use <id>)")
    return ContainerClient(_session(ctx), int(eid))


@container.command("list")
@click.option("--all", "all_", is_flag=True, default=False)
@pass_ctx
def container_list(ctx, all_):
    """List containers."""
    try:
        _out(ctx, _container_client(ctx).list(all=all_))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("inspect")
@click.argument("container_id")
@pass_ctx
def container_inspect(ctx, container_id):
    """Inspect a container."""
    try:
        _out(ctx, _container_client(ctx).inspect(container_id))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("start")
@click.argument("container_id")
@pass_ctx
def container_start(ctx, container_id):
    """Start a container."""
    try:
        _container_client(ctx).start(container_id)
        _out(ctx, {"message": f"Container {container_id} started"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("stop")
@click.argument("container_id")
@click.option("--timeout", default=10, type=int)
@pass_ctx
def container_stop(ctx, container_id, timeout):
    """Stop a container."""
    try:
        _container_client(ctx).stop(container_id, timeout=timeout)
        _out(ctx, {"message": f"Container {container_id} stopped"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("restart")
@click.argument("container_id")
@click.option("--timeout", default=10, type=int)
@pass_ctx
def container_restart(ctx, container_id, timeout):
    """Restart a container."""
    try:
        _container_client(ctx).restart(container_id, timeout=timeout)
        _out(ctx, {"message": f"Container {container_id} restarted"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("kill")
@click.argument("container_id")
@click.option("--signal", "sig", default="SIGKILL")
@pass_ctx
def container_kill(ctx, container_id, sig):
    """Kill a container."""
    try:
        _container_client(ctx).kill(container_id, signal=sig)
        _out(ctx, {"message": f"Container {container_id} killed with {sig}"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("remove")
@click.argument("container_id")
@click.option("--force", is_flag=True, default=False)
@click.option("--volumes", is_flag=True, default=False)
@pass_ctx
def container_remove(ctx, container_id, force, volumes):
    """Remove a container."""
    try:
        _container_client(ctx).remove(container_id, force=force, volumes=volumes)
        _out(ctx, {"message": f"Container {container_id} removed"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("logs")
@click.argument("container_id")
@click.option("--tail", default=100, type=int)
@click.option("--stdout/--no-stdout", default=True)
@click.option("--stderr/--no-stderr", default=True)
@pass_ctx
def container_logs(ctx, container_id, tail, stdout, stderr):
    """Fetch container logs."""
    try:
        result = _container_client(ctx).logs(container_id, tail=tail, stdout=stdout, stderr=stderr)
        if ctx.get("json"):
            _out(ctx, {"logs": result})
        else:
            click.echo(result)
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("stats")
@click.argument("container_id")
@pass_ctx
def container_stats(ctx, container_id):
    """Get container resource stats."""
    try:
        _out(ctx, _container_client(ctx).stats(container_id))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("top")
@click.argument("container_id")
@pass_ctx
def container_top(ctx, container_id):
    """List running processes in a container."""
    try:
        _out(ctx, _container_client(ctx).top(container_id))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@container.command("recreate")
@click.argument("container_id")
@click.option("--pull/--no-pull", default=True)
@pass_ctx
def container_recreate(ctx, container_id, pull):
    """Recreate a container (optionally pulling latest image)."""
    try:
        _out(ctx, _container_client(ctx).recreate(container_id, pull_image=pull))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# image group
# ---------------------------------------------------------------------------

@main.group()
def image():
    """Manage images via Docker proxy."""


def _image_client(ctx) -> ImageClient:
    cfg = _cfg(ctx)
    eid = ctx.get("env_id") or cfg._data.get("env_id")
    if not eid:
        raise click.UsageError("--env-id required (or set with: env use <id>)")
    return ImageClient(_session(ctx), int(eid))


@image.command("list")
@pass_ctx
def image_list(ctx):
    """List images."""
    try:
        _out(ctx, _image_client(ctx).list())
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@image.command("inspect")
@click.argument("image_name")
@pass_ctx
def image_inspect(ctx, image_name):
    """Inspect an image."""
    try:
        _out(ctx, _image_client(ctx).inspect(image_name))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@image.command("pull")
@click.argument("image_name")
@click.option("--tag", default="latest")
@pass_ctx
def image_pull(ctx, image_name, tag):
    """Pull an image."""
    try:
        _out(ctx, _image_client(ctx).pull(image_name, tag=tag))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@image.command("remove")
@click.argument("image_name")
@click.option("--force", is_flag=True, default=False)
@pass_ctx
def image_remove(ctx, image_name, force):
    """Remove an image."""
    try:
        _out(ctx, _image_client(ctx).remove(image_name, force=force))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@image.command("tag")
@click.argument("image_name")
@click.argument("repo")
@click.option("--tag", default="latest")
@pass_ctx
def image_tag(ctx, image_name, repo, tag):
    """Tag an image."""
    try:
        _image_client(ctx).tag(image_name, repo=repo, tag=tag)
        _out(ctx, {"message": f"Tagged {image_name} as {repo}:{tag}"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@image.command("prune")
@pass_ctx
def image_prune(ctx):
    """Remove dangling images."""
    try:
        _out(ctx, _image_client(ctx).prune())
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# volume group
# ---------------------------------------------------------------------------

@main.group()
def volume():
    """Manage volumes via Docker proxy."""


def _volume_client(ctx) -> VolumeClient:
    cfg = _cfg(ctx)
    eid = ctx.get("env_id") or cfg._data.get("env_id")
    if not eid:
        raise click.UsageError("--env-id required (or set with: env use <id>)")
    return VolumeClient(_session(ctx), int(eid))


@volume.command("list")
@pass_ctx
def volume_list(ctx):
    """List volumes."""
    try:
        _out(ctx, _volume_client(ctx).list())
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@volume.command("inspect")
@click.argument("name")
@pass_ctx
def volume_inspect(ctx, name):
    """Inspect a volume."""
    try:
        _out(ctx, _volume_client(ctx).inspect(name))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@volume.command("create")
@click.argument("name")
@click.option("--driver", default="local")
@pass_ctx
def volume_create(ctx, name, driver):
    """Create a volume."""
    try:
        _out(ctx, _volume_client(ctx).create(name, driver=driver))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@volume.command("remove")
@click.argument("name")
@click.option("--force", is_flag=True, default=False)
@pass_ctx
def volume_remove(ctx, name, force):
    """Remove a volume."""
    try:
        _volume_client(ctx).remove(name, force=force)
        _out(ctx, {"message": f"Volume {name} removed"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@volume.command("prune")
@pass_ctx
def volume_prune(ctx):
    """Remove unused volumes."""
    try:
        _out(ctx, _volume_client(ctx).prune())
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# network group
# ---------------------------------------------------------------------------

@main.group()
def network():
    """Manage networks via Docker proxy."""


def _network_client(ctx) -> NetworkClient:
    cfg = _cfg(ctx)
    eid = ctx.get("env_id") or cfg._data.get("env_id")
    if not eid:
        raise click.UsageError("--env-id required (or set with: env use <id>)")
    return NetworkClient(_session(ctx), int(eid))


@network.command("list")
@pass_ctx
def network_list(ctx):
    """List networks."""
    try:
        _out(ctx, _network_client(ctx).list())
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@network.command("inspect")
@click.argument("network_id")
@pass_ctx
def network_inspect(ctx, network_id):
    """Inspect a network."""
    try:
        _out(ctx, _network_client(ctx).inspect(network_id))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@network.command("create")
@click.argument("name")
@click.option("--driver", default="bridge")
@pass_ctx
def network_create(ctx, name, driver):
    """Create a network."""
    try:
        _out(ctx, _network_client(ctx).create(name, driver=driver))
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@network.command("remove")
@click.argument("network_id")
@pass_ctx
def network_remove(ctx, network_id):
    """Remove a network."""
    try:
        _network_client(ctx).remove(network_id)
        _out(ctx, {"message": f"Network {network_id} removed"})
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@network.command("prune")
@pass_ctx
def network_prune(ctx):
    """Remove unused networks."""
    try:
        _out(ctx, _network_client(ctx).prune())
    except (ConfigError, APIError, click.UsageError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# user group
# ---------------------------------------------------------------------------

@main.group()
def user():
    """Manage Portainer users."""


@user.command("list")
@pass_ctx
def user_list(ctx):
    """List all users."""
    try:
        _out(ctx, UserClient(_session(ctx)).list())
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("me")
@pass_ctx
def user_me(ctx):
    """Show current user info."""
    try:
        _out(ctx, UserClient(_session(ctx)).me())
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("get")
@click.argument("user_id", type=int)
@pass_ctx
def user_get(ctx, user_id):
    """Get user details."""
    try:
        _out(ctx, UserClient(_session(ctx)).get(user_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("create")
@click.option("--username", required=True)
@click.option("--password", required=True, hide_input=True, prompt=True)
@click.option("--role", default=2, type=int, help="1=admin, 2=regular")
@pass_ctx
def user_create(ctx, username, password, role):
    """Create a new user."""
    try:
        _out(ctx, UserClient(_session(ctx)).create(username, password, role=role))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("delete")
@click.argument("user_id", type=int)
@pass_ctx
def user_delete(ctx, user_id):
    """Delete a user."""
    try:
        UserClient(_session(ctx)).delete(user_id)
        _out(ctx, {"message": f"User {user_id} deleted"})
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("memberships")
@click.argument("user_id", type=int)
@pass_ctx
def user_memberships(ctx, user_id):
    """List team memberships for a user."""
    try:
        _out(ctx, UserClient(_session(ctx)).list_memberships(user_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("create-api-key")
@click.argument("user_id", type=int)
@click.option("--description", required=True)
@pass_ctx
def user_create_api_key(ctx, user_id, description):
    """Create an API key for a user."""
    try:
        _out(ctx, UserClient(_session(ctx)).create_api_key(user_id, description))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@user.command("list-api-keys")
@click.argument("user_id", type=int)
@pass_ctx
def user_list_api_keys(ctx, user_id):
    """List API keys for a user."""
    try:
        _out(ctx, UserClient(_session(ctx)).list_api_keys(user_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# team group
# ---------------------------------------------------------------------------

@main.group()
def team():
    """Manage Portainer teams."""


@team.command("list")
@pass_ctx
def team_list(ctx):
    """List all teams."""
    try:
        _out(ctx, TeamClient(_session(ctx)).list())
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@team.command("get")
@click.argument("team_id", type=int)
@pass_ctx
def team_get(ctx, team_id):
    """Get team details."""
    try:
        _out(ctx, TeamClient(_session(ctx)).get(team_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@team.command("create")
@click.argument("name")
@pass_ctx
def team_create(ctx, name):
    """Create a new team."""
    try:
        _out(ctx, TeamClient(_session(ctx)).create(name))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@team.command("delete")
@click.argument("team_id", type=int)
@pass_ctx
def team_delete(ctx, team_id):
    """Delete a team."""
    try:
        TeamClient(_session(ctx)).delete(team_id)
        _out(ctx, {"message": f"Team {team_id} deleted"})
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@team.command("members")
@click.argument("team_id", type=int)
@pass_ctx
def team_members(ctx, team_id):
    """List team members."""
    try:
        _out(ctx, TeamClient(_session(ctx)).list_memberships(team_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@team.command("add-member")
@click.argument("team_id", type=int)
@click.argument("user_id", type=int)
@click.option("--role", default=2, type=int, help="1=leader, 2=member")
@pass_ctx
def team_add_member(ctx, team_id, user_id, role):
    """Add a user to a team."""
    try:
        _out(ctx, TeamClient(_session(ctx)).add_member(team_id, user_id, role=role))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# registry group
# ---------------------------------------------------------------------------

@main.group()
def registry():
    """Manage container registries."""


@registry.command("list")
@pass_ctx
def registry_list(ctx):
    """List all registries."""
    try:
        _out(ctx, RegistryClient(_session(ctx)).list())
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@registry.command("get")
@click.argument("registry_id", type=int)
@pass_ctx
def registry_get(ctx, registry_id):
    """Get registry details."""
    try:
        _out(ctx, RegistryClient(_session(ctx)).get(registry_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@registry.command("create")
@click.option("--name", required=True)
@click.option("--url", required=True)
@click.option("--type", "reg_type", default=1, type=int, help="1=custom, 6=DockerHub")
@click.option("--username", default=None)
@click.option("--password", default=None)
@pass_ctx
def registry_create(ctx, name, url, reg_type, username, password):
    """Add a registry."""
    try:
        _out(ctx, RegistryClient(_session(ctx)).create(
            name, url, registry_type=reg_type, username=username, password=password))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@registry.command("delete")
@click.argument("registry_id", type=int)
@pass_ctx
def registry_delete(ctx, registry_id):
    """Delete a registry."""
    try:
        RegistryClient(_session(ctx)).delete(registry_id)
        _out(ctx, {"message": f"Registry {registry_id} deleted"})
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


@registry.command("repositories")
@click.argument("registry_id", type=int)
@pass_ctx
def registry_repositories(ctx, registry_id):
    """List repositories in a registry."""
    try:
        _out(ctx, RegistryClient(_session(ctx)).list_repositories(registry_id))
    except (ConfigError, APIError) as e:
        _err(ctx, str(e))
        sys.exit(1)


# ---------------------------------------------------------------------------
# repl
# ---------------------------------------------------------------------------

@main.command()
@pass_ctx
def repl(ctx):
    """Interactive REPL for cli-anything-portainer."""
    click.echo("cli-anything-portainer REPL (type 'exit' to quit)")
    while True:
        try:
            line = click.prompt("portainer", prompt_suffix="> ")
        except (click.Abort, EOFError):
            break
        line = line.strip()
        if not line or line in ("exit", "quit"):
            break
        try:
            args = shlex.split(line)
            main.main(args, standalone_mode=False, obj=ctx)
        except SystemExit:
            pass
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    main()
