# Kali AI Repository Node

Kali is a first-class Macintosh homelab node for Linux-side AI and cybersecurity work.

## Role in the System

Kali is not an isolated experiment VM. It is a deliberate platform node with two functions:
- **AI Repository Node**: central Linux-side base for model/tooling/runtime workflows
- **Cybersecurity Node**: controlled environment for security tooling and hardening operations

## Access Contract

Primary operator contract:
- from Mac terminal, run `ssh kali`
- connect through Tailscale-backed private networking
- land directly in Kali shell for immediate operation

Design intent:
- no cognitive overhead
- no repeated host/IP lookup
- one canonical remote command

## Why This Node Exists

- keeps Linux-native AI runtime concerns out of local Mac clutter
- provides a stable remote target for anywhere-access operations
- allows infrastructure experimentation without disrupting local dev flow

## Node Responsibilities

Typical responsibilities on Kali:
- AI model/runtime setup and repository management
- Linux-based automation helpers and scripts
- security tooling, diagnostics, and hardening tasks
- remote operations from any approved terminal client

## OpenCode + Ollama Baseline

Kali is configured to run OpenCode against local Ollama.

Current target models:
- `nexusriot/Qwen3.5-Uncensored-HauhauCS-Aggressive:4b`
- `huihui_ai/deepseek-r1-abliterated:7b`

OpenCode config path:
- `/root/.config/opencode/opencode.json`

Instruction files:
- `/root/.config/opencode/instructions/macintosh-role.md`
- `/root/.config/opencode/instructions/pkb-bridge.md`

Notes:
- `nexusriot/Qwen3.5-Uncensored-HauhauCS-Aggressive:4b` is currently the OpenCode tool-call model on Kali (validated via `/v1/chat/completions` tool call response).
- `huihui_ai/deepseek-r1-abliterated:7b` currently does not expose OpenAI-style tool calling in Ollama, so it is suitable for coding/reasoning completions but not tool-call JSON workflows.
- model latency depends heavily on whether GPU offload is enabled on the VM.

## Brain/PKB Session Sync

Kali OpenCode sessions are synced from Mac into the Brain vault as raw conversation sources.

Sync script (Mac):
- `homelab/scripts/sync-kali-opencode-to-brain.sh`

Output location:
- `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/Raw/Conversations/Kali OpenCode/`

Local sync state:
- `homelab/.state/kali-opencode-synced-sessions.txt`

Recommended automation:
- LaunchAgent on Mac to run the sync script on a short interval (for near-real-time PKB capture).

## Relationship to Agent Hub

Kali and Agent Hub are complementary:
- Agent Hub runs the approval-safe automation graph
- Kali provides a flexible Linux operations surface for AI/security workflows

Either can call into shared services when needed, but they remain separate concerns.

## Minimal Operator Experience

1. Open local terminal.
2. Run `ssh kali`.
3. Execute Linux-side AI/security work.
4. Exit when done.

This is the expected everyday flow.

## Visual Anchor

- **Image #2 (Proxmox install console)** marks the initial provisioning stage of this node.
