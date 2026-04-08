# Test Results — cli-anything-portainer

## Run: 2026-04-07

```text
platform win32 -- Python 3.14.3, pytest-9.0.3
```

### Unit Tests (`test_core.py`)

```text
65 passed in 0.33s
```

Coverage:

- `TestConfig` (10 tests) — file I/O, env var overrides, token masking, header generation
- `TestOutputFormatter` (5 tests) — JSON and human modes
- `TestAPIError` (1 test)
- `TestPortainerSession` (4 tests) — URL construction, error raising
- `TestEnvironmentClient` (5 tests) — list with both response formats, get, snapshot
- `TestStackClient` (5 tests) — list with/without filter, get, delete
- `TestContainerClient` (8 tests) — Docker proxy path, list, start, stop, remove, logs
- `TestImageClient` (4 tests) — list, pull, remove, prune
- `TestVolumeClient` (4 tests) — list (dict + list response), create, remove
- `TestNetworkClient` (3 tests) — list, create with labels, prune
- `TestUserClient` (6 tests) — list, me, create, delete, change_password, create_api_key
- `TestTeamClient` (5 tests) — list, create, delete, add_member, list_memberships
- `TestRegistryClient` (5 tests) — list, create (with/without auth), delete, list_repositories

### E2E / Subprocess Tests (`test_full_e2e.py`)

```text
21 passed in 8.55s  (live: https://192.168.1.20:9443, self-signed cert, API key auth)
```

- `TestSubprocessHelp` (11 tests) — `--help` for all command groups
- `TestSubprocessConfig` (3 tests) — config set/show, graceful failure without server
- `TestLiveEnvs` (2 tests) — env list, env get
- `TestLiveStacks` (1 test) — stack list (env 2: Optimus-Qnap, 50 stacks)
- `TestLiveContainers` (1 test) — container list (60 running)
- `TestLiveImages` (1 test) — image list (1305 images)
- `TestLiveUsers` (2 tests) — user me, user list

### Total

| Category       | Passed | Skipped | Failed |
|----------------|--------|---------|--------|
| Unit           | 65     | 0       | 0      |
| E2E/Subprocess | 21     | 0       | 0      |
| **Total**      | **86** | **0**   | **0**  |

## Live server

- URL: `https://192.168.1.20:9443`
- Auth: API key (`ptr_` prefix) via `X-API-Key` header
- SSL: self-signed cert (`ssl_verify=False`)
- Environments: Optimus-Qnap (id=2), Zeus-Unraid (id=4), Apollo-Proxmox (id=9)

## To run live tests

```bash
export PORTAINER_URL=https://192.168.1.20:9443
export PORTAINER_TOKEN=<api_key>
export PORTAINER_SSL_VERIFY=false
python -m pytest cli_anything/portainer/tests/ -v
```
