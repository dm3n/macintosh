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
