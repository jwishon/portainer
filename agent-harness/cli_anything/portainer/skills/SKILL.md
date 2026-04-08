---
name: cli-anything-portainer
description: CLI harness for Portainer container management — environments, stacks, containers, images, volumes, networks, users, teams, registries
---

# cli-anything-portainer

## Installation & Setup

```bash
cd portainer/agent-harness && pip install -e .

# Configure
cli-anything-portainer config set --url https://portainer.example.com \
  --username admin --password secret
cli-anything-portainer login
```

## Key Commands

```bash
# Environments
cli-anything-portainer env list
cli-anything-portainer env use 1              # sets default env_id

# Stacks
cli-anything-portainer --env-id 1 stack list
cli-anything-portainer --env-id 1 stack deploy --name myapp --file docker-compose.yml
cli-anything-portainer --env-id 1 stack redeploy <stack_id>

# Containers
cli-anything-portainer --env-id 1 container list --all
cli-anything-portainer --env-id 1 container logs <id> --tail 100
cli-anything-portainer --env-id 1 container restart <id>
cli-anything-portainer --env-id 1 container recreate <id>

# Images
cli-anything-portainer --env-id 1 image list
cli-anything-portainer --env-id 1 image pull nginx --tag latest

# Volumes / Networks
cli-anything-portainer --env-id 1 volume list
cli-anything-portainer --env-id 1 network list

# Users & Teams (admin)
cli-anything-portainer user list
cli-anything-portainer team list

# JSON output
cli-anything-portainer --json env list | jq '.data[].Name'
```

## Architecture

- Auth: JWT via `POST /api/auth`, stored in `~/.config/cli-anything-portainer/config.json`
- Docker proxy: `/api/endpoints/{id}/docker/...` for container/image/volume/network ops
- `--env-id` or `PORTAINER_ENV_ID` env var required for Docker proxy commands
