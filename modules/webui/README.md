# WebUI Module

Provides the Open-WebUI chat interface, pre-configured to use LiteLLM as its
model backend.

## Services

### open-webui
Browser-based chat UI accessible via Traefik at `https://<your-domain>`. Talks
to LiteLLM for model requests and uses the shared Postgres instance for user
data and chat history.

## Configuration

Settings are split between the root `.env` (for keys shared with other modules)
and this module's `.env`.

### Auth & Access (`modules/webui/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_SIGNUP` | `true` | Allow new users to register without an auth provider |
| `DEFAULT_USER_ROLE` | `user` | Role assigned to new signups (`user` or `admin`) |
| `ENABLE_API_KEY` | `false` | Let users generate API keys to proxy requests through the WebUI from other apps |
| `WEBUI_NAME` | *(commented out)* | Custom name shown on the login screen |

### SSO / OAuth

To enable SSO, set `ENABLE_OAUTH_SIGNUP=true` and fill in the following:

| Variable | Description |
|----------|-------------|
| `OAUTH_CLIENT_ID` | OAuth app client ID |
| `OAUTH_CLIENT_SECRET` | OAuth app client secret |
| `OPENID_PROVIDER_URL` | OpenID Connect discovery URL (e.g. `https://your-idp/.well-known/openid-configuration`) |
| `OAUTH_PROVIDER_NAME` | Label shown on the SSO login button |
| `OAUTH_SCOPES` | Scopes to request (e.g. `openid email profile`) |
| `OAUTH_MERGE_ACCOUNTS_BY_EMAIL` | Merge SSO accounts with existing local accounts that share the same email |

### Model Backend

By default, Open-WebUI is pointed at LiteLLM using the master key from the root
`.env`. These can be overridden in `modules/webui/.env` if needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_BASE_URL` | `http://litellm:8000/v1` | URL of the model API |
| `OPENAI_API_KEY` | `${LITELLM_MASTER_KEY}` | API key for the model backend |

## WebUI Functions

The `webui_functions/` directory contains Open-WebUI plugin functions that run
on every request. See [`webui_functions/README.md`](webui_functions/README.md)
for details on each function.

At a glance:

| File | Purpose |
|------|---------|
| `litellm_end_user.py` | Passes the user's email and session ID to LiteLLM for per-user cost tracking |
| `langfuse_integration.py` | Logs prompts and responses to Langfuse (v2 API) |
| `langfuse_v3_integration.py` | Logs prompts and responses to Langfuse (v3+ API) |

Only one Langfuse integration should be active at a time. Both are inactive by
default unless Langfuse credentials are configured. Even though these are
included, they are not guaranteed to work as all of these services move too
fast to regularly keep up with.
