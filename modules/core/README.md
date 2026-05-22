# Core Module

Provides the shared infrastructure that all other modules depend on: TLS
termination and routing via Traefik, the LiteLLM API gateway, and a Postgres
database.

## Services

### Traefik
Reverse proxy that handles TLS termination and routes incoming traffic to the
appropriate service. All other services are exposed through Traefik rather than
binding ports directly.

Exposed ports:
- `80` — HTTP, redirects to HTTPS
- `443` — HTTPS (open-webui, Grafana)
- `8000` — LiteLLM API endpoint
- `8080` — Traefik dashboard (see `traefik/conf/traefik.yaml` for auth config)

TLS config is in `traefik/conf/dynamic/tls.yaml`. Certificates are read from
`certs/certfile.crt` and `certs/keyfile.key`. New services get routed
automatically when they add the appropriate Traefik labels — no need to touch
the Traefik config directly.

### LiteLLM
OpenAI-compatible API gateway that routes requests to one or more inference
backends. Configured via `litellm-config.yml`.

To add or change routed models, edit `litellm-config.yml`. Each entry maps a
`model_name` (what clients request) to a backend (`api_base` + `model`). The
current default routes `gpt-oss-120b` to the local vLLM instance:

```yaml
model_list:
  - model_name: gpt-oss-120b
    litellm_params:
      api_base: http://vllm:8000/v1
      api_key: LiteLLM
      model: openai/gpt-oss-120b # `openai/` indicates the `api_base` is OpenAI compatible
```

LiteLLM also optionally forwards request data to Langfuse for logging — set
`LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_SECRET_KEY` in `.env` to
enable this if you are already hosting a Langfuse instance. Otherwise, either
forget about logging, wait for it to be added, or submit a PR.

### Postgres (`core-postgres`)
Shared database used by LiteLLM (routing state, cost tracking). Not exposed
externally. Data is persisted in the `core-database-data` Docker volume.

### Portainer (dev profile only)
Container management UI. Only starts when the `dev` profile is active:

```bash
docker compose --profile dev up -d
```

Accessible at `https://<host>:9443`.

## Configuration

All configurable values are in `.env`:

| Variable | Description |
|----------|-------------|
| `LITELLM_MASTER_KEY` | LiteLLM admin password and API key |
| `LITELLM_SALT_KEY` | Cryptographic salt for LiteLLM |
| `POSTGRES_USER` | Postgres username |
| `POSTGRES_PASSWORD` | Postgres password |
| `DATABASE_URL` | Full Postgres connection string — auto-built from user/password above |
| `LANGFUSE_HOST` | Langfuse instance URL — leave blank to disable |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key |
| `LITELLM_VERSION` | LiteLLM Docker image version |
| `DB_VERSION` | Postgres Docker image version |
| `TRAEFIK_VERSION` | Traefik Docker image version |

Run `./install.sh` from the repo root to be prompted for all required values interactively.

## TLS Certificates

Place your certificate and private key in `certs/` named `certfile.crt` and
`keyfile.key`.
