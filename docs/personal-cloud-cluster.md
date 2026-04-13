# Personal Cloud 2 Cluster (Proxmox)

This is the infrastructure layer of Macintosh: your private server compute pool where persistent runtime services live.

## Purpose

- host always-available workloads independent of the Mac
- provide virtualization and resource isolation
- support AI infrastructure and automation workloads

## Platform Model

```text
Cluster resource pool
  -> Proxmox (virtualization/host control)
  -> VM and container workloads
  -> service runtime + data state
```

Key principles:
- workloads are explicit and documented
- runtime state is durable
- approval gates protect external actions

## Main Workload Groups

### 1) Kali VM Node
- dedicated Linux node for AI repository and cybersecurity operations
- remote entrypoint from Mac and remote terminals via SSH over Tailscale

### 2) Agent Hub Runtime
- orchestrator dispatches/schedules
- approval gateway syncs decisions via Linear
- executor performs only approved actions
- MCP gateway abstracts integrations
- domain agents create pending actions

### 3) State Services
- Postgres for workflow/approval/audit state
- Redis for queue/signaling

## Control and Safety

Approval model remains central:
- agents draft pending actions
- Linear is the approval interface
- executor delivers only approved actions
- audit trail captures lifecycle events

## Operational Access

The cluster is managed from local terminals and controlled scripts:
- deploy/update via `homelab/scripts/deploy.sh`
- local debugging via SSH tunnel script
- direct VM operations in Proxmox when needed

## Visual Anchor

- **Image #2 (Proxmox)** represents this layer: VM-level operations and Kali provisioning inside cluster infrastructure.
