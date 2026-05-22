# Inference Module

This module runs the local LLM inference stack: vLLM for model serving, Prometheus for metrics collection, and Grafana for visualization.

## Services

### vLLM
Hosts the local model and exposes an OpenAI-compatible API on port 8000 to
other containers (not exposed outside docker). LiteLLM (in the core module)
routes inference requests to this service.

The current default configuration serves `openai/gpt-oss-120b` on GPU 0. This
model requires roughly 80 GB of VRAM; if your GPU has less, edit
`docker-compose.infer-servers.yml` to serve a smaller model.

Model weights are loaded from `~/.cache/huggingface/hub/` on the host. The
harmony tokenizer cache is mounted from `~/.cache/harmony/`.

> Note: If there are any issues with hosting gpt-oss, double check that the
> Harmony chat template is properly adhered to when the prompt is formatted
> before being passed to the model internally in the vLLM codebase. Several
> Harmony-based format issues were uncovered while developing this project.

### Prometheus
Scrapes vLLM metrics every 5 seconds from `vllm:8000`. Not exposed externally —
Grafana reads from it internally.

### Grafana
Visualizes vLLM metrics via the pre-configured `prometheus-vllm` datasource.
Accessible via Traefik at `https://grafana.<your-domain>`. Dashboards are
provisioned from `grafana/dashboards/`.

## Configuration

All configurable values are in `.env`:

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | Hugging Face API token — required for gated models |
| `VLLM_VERSION` | vLLM Docker image version |
| `GRAFANA_VERSION` | Grafana Docker image version |
| `PROMETHEUS_VERSION` | Prometheus Docker image version |

## Changing the Model

To change which model vLLM serves, edit `docker-compose.infer-servers.yml`. The
`command:` block passes arguments directly to vLLM. At minimum, update
`--model` and `--served-model-name`, then update
`modules/core/litellm-config.yml` to route requests to the new model name.

To add a second inference server (e.g., for a different model or for load
balancing), add a new service to `docker-compose.infer-servers.yml` using the
`<<: *vllm_defaults` anchor and assign it a different GPU via `device_ids`.
Then update `modules/core/litellm-config.yml` to route requests to the new
model name.
