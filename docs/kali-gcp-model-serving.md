# Kali OpenCode -> GCP GPU Model Serving

This setup keeps Kali as the operator/runtime node and moves model inference to a GCP GPU VM.

## Current Deployment

- GCP project: `nodebase-473513`
- VM: `ollama-gpu-1`
- Zone: `us-central1-a`
- Reserved static IP: `35.239.94.39`
- Serving API: `http://35.239.94.39:11434/v1`

Models served from GCP Ollama:
- `nexusriot/Qwen3.5-Uncensored-HauhauCS-Aggressive:4b`
- `huihui_ai/deepseek-r1-abliterated:7b`

OpenCode config on Kali:
- `/root/.config/opencode/opencode.json`
- provider `local-ollama` points to `http://35.239.94.39:11434/v1`

## Auto Start/Stop Behavior

Kali wrapper path:
- `/usr/local/bin/opencode-gcp`

Symlinked as default command:
- `/usr/local/bin/opencode -> /usr/local/bin/opencode-gcp`

Behavior:
1. Running `opencode` on Kali starts `ollama-gpu-1` if it is stopped.
2. Wrapper waits until `GET /v1/models` is reachable.
3. On process exit, a delayed idle check runs.
4. If there are no active SSH sessions, the GPU VM is stopped.

Default stop grace:
- `120s`
- override per run:
  - `OPENCODE_GCP_STOP_GRACE_SECONDS=30 opencode`

## Notes

- Firewall ingress to port `11434` should stay restricted to trusted source IPs.
- The static IP avoids endpoint breakage after VM restarts.
- Kali/Proxmox infrastructure remains unchanged; only model inference is offloaded.
