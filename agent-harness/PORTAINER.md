# cli-anything-portainer SOP

## Purpose
Full CLI harness for Portainer CE — manage environments, stacks, containers, images, volumes,
networks, users, teams, and registries from the command line.

## Installation
```bash
cd portainer/agent-harness
pip install -e .
```

## Configuration
```bash
# Set URL and credentials
cli-anything-portainer config set --url https://portainer.example.com --username admin --password secret

# Log in (obtains JWT, stored in ~/.config/cli-anything-portainer/config.json)
cli-anything-portainer login

# Or pass token directly
cli-anything-portainer config set --token <jwt>

# Environment variables override config
export PORTAINER_URL=https://portainer.example.com
export PORTAINER_TOKEN=<jwt>
export PORTAINER_ENV_ID=1
```

## Quick Start
```bash
# List environments
cli-anything-portainer env list

# Set default environment
cli-anything-portainer env use 1

# List stacks in env 1
cli-anything-portainer --env-id 1 stack list

# List running containers
cli-anything-portainer --env-id 1 container list

# Get logs
cli-anything-portainer --env-id 1 container logs <container_id> --tail 50

# Deploy a stack
cli-anything-portainer --env-id 1 stack deploy --name myapp --file docker-compose.yml

# JSON output
cli-anything-portainer --json env list
```

## Command Groups

| Group       | Commands                                                    |
|-------------|-------------------------------------------------------------|
| `login`     | Authenticate, store JWT                                     |
| `logout`    | Invalidate token                                            |
| `config`    | `set`, `show`                                               |
| `env`       | `list`, `get`, `snapshot`, `use`                            |
| `stack`     | `list`, `get`, `file`, `deploy`, `update`, `delete`, `start`, `stop`, `redeploy` |
| `container` | `list`, `inspect`, `start`, `stop`, `restart`, `kill`, `remove`, `logs`, `stats`, `top`, `recreate` |
| `image`     | `list`, `inspect`, `pull`, `remove`, `tag`, `prune`         |
| `volume`    | `list`, `inspect`, `create`, `remove`, `prune`              |
| `network`   | `list`, `inspect`, `create`, `remove`, `prune`              |
| `user`      | `list`, `me`, `get`, `create`, `delete`, `memberships`, `create-api-key`, `list-api-keys` |
| `team`      | `list`, `get`, `create`, `delete`, `members`, `add-member`  |
| `registry`  | `list`, `get`, `create`, `delete`, `repositories`           |
| `repl`      | Interactive REPL                                            |

## Architecture

```
portainer/agent-harness/
├── setup.py
├── PORTAINER.md
└── cli_anything/portainer/
    ├── __init__.py
    ├── portainer_cli.py          # Click CLI entry point
    ├── utils/
    │   ├── config.py             # Config (file + env vars)
    │   └── output.py             # OutputFormatter
    └── core/
        ├── session.py            # HTTP session, APIError
        ├── auth.py               # login() / logout()
        ├── environments.py       # EnvironmentClient
        ├── stacks.py             # StackClient
        ├── containers.py         # ContainerClient (Docker proxy)
        ├── images.py             # ImageClient (Docker proxy)
        ├── volumes.py            # VolumeClient (Docker proxy)
        ├── networks.py           # NetworkClient (Docker proxy)
        ├── users.py              # UserClient
        ├── teams.py              # TeamClient
        └── registries.py         # RegistryClient
```

## Notes
- Docker operations (container/image/volume/network) go through `/api/endpoints/{id}/docker/...`
- `--env-id` flag or `PORTAINER_ENV_ID` env var needed for Docker proxy commands
- JWT auth via `POST /api/auth`; token stored in `~/.config/cli-anything-portainer/config.json`
