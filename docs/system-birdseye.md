# Macintosh System Bird's-Eye

This is the operating map of Macintosh as a productized personal engineering system.

## Core Purpose

Macintosh exists to do three things at once:
- ship software fast with AI coding agents
- preserve and compound knowledge over time (PKB/Brain)
- run approval-safe automation and AI infrastructure on personal cloud servers

## Top-Level Architecture

```text
Mac (local operator environment)
  -> Superset terminal for coding
  -> Warp terminal for general terminal work
  -> CLI coding agents: Codex, Claude, Gemini, OpenCode
  -> Local dev repos + shared agent standards + superpowers + PKB workflows
  -> Tailscale secure mesh

Personal Cloud 2 (cluster resource pool)
  -> Proxmox virtualization layer
  -> VM/service workloads
     -> Kali VM (AI Repository + Cybersecurity node)
     -> Postgres + Redis state

Control Boundary
  -> Linear approval gate before external writes
```

## Product View

### 1) Local Development System (Mac)
Your Mac is the daily control surface and primary development workstation.

- Coding experience is terminal-first
- Superset is used for implementation-focused coding sessions
- Warp is used for general-purpose terminal tasks
- Four coding agents are available with aligned context and standards
- Brain/PKB system is local-first with iCloud-backed persistence

See: [Dev Environment](dev-environment.md), [Local Development System](local-development-system.md), [Knowledge Brain](knowledge-brain.md), [Superpowers](superpowers.md)

### 2) Personal Cloud 2 Cluster (Proxmox)
Your personal cloud cluster is the always-available infrastructure substrate.

- Proxmox manages compute virtualization
- Cluster nodes host service VMs and runtime workloads

See: [Homelab Architecture](homelab-architecture.md), [Personal Cloud Cluster](personal-cloud-cluster.md), [Setup](setup.md)

### 3) Kali VM Node (AI Repository + Cybersecurity)
Kali is now a first-class node in the homelab model.

- Central Linux target for AI model/tooling repository workflows
- Cybersecurity experimentation and operational hardening node
- Reachable remotely over Tailscale + SSH from any terminal
- Operator UX target: one command from Mac: `ssh kali`

See: [Kali AI Repository Node](kali-ai-repository-node.md)

## Operator Story (How It Feels)

1. Build locally on Mac with your preferred coding agent in Superset.
2. Use PKB context continuously so decisions persist beyond a single session.
3. Jump to infrastructure instantly via `ssh kali` when Linux-side model/runtime work is needed.
4. Keep automation safe: all external writes stay behind explicit approval.
5. Maintain one coherent system instead of fragmented tools.

See: [Operator Workflows](operator-workflows.md)

## Screenshot Anchors From Current Setup

These screenshots map to key layers of the system:
- **Image #1**: PKB graph view in the Brain vault (knowledge layer)
- **Image #2**: Proxmox VM console while Kali node is being installed (infrastructure layer)
- **Image #3**: Superset multi-agent coding workspace (local development layer)

Use these visuals as orientation points when onboarding the stack.
