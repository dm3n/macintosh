# Tech Stack

Complete catalogue of every tool in the personal and company stack, organised by function.

---

## AI & Intelligence

| Tool | Role | Why |
|------|------|-----|
| **Claude Code** | Primary development environment | AI-native terminal IDE — architects, codes, reviews, and deploys. Agents handle full implementation loops. |
| **Claude (claude.ai)** | Strategy, writing, research | Complex reasoning, pitch drafting, market analysis, long-context work |
| **Perplexity** | Live internet research | Real-time competitor monitoring, news, market intelligence with citations |
| **Gemini 3 Flash** | In-product AI (Airbank) | Document extraction, QoE analysis via Vertex AI |
| **Vertex AI** | AI infrastructure (Airbank) | RAG corpus management, Gemini model serving, GCP integration |

---

## Development

| Tool | Role | Why |
|------|------|-----|
| **Superset + Zsh** | Terminal | Fast shell workflow with persistent sessions and split panes |
| **GitHub** | Version control + code hosting | All repos — private (Airbank products) and public (open source) |
| **Vercel** | Deployment | Zero-config Next.js deploys, preview URLs per PR, edge network |
| **Linear** | Project management | Dev sprints, issue tracking, GitHub PR integration, roadmap |

**Standard project stack:**
```
Next.js 16  ·  React 19  ·  TypeScript  ·  Tailwind v4  ·  shadcn/ui
```
Every project uses shadcn/ui for all UI components — no exceptions.

---

## Knowledge & Documentation

| Tool | Role | Why |
|------|------|-----|
| **Obsidian** | Persistent AI brain | Graph-linked markdown vault. Cross-session memory for Claude Code and all AI models. |
| **Notion** | Company knowledge base | SOPs, meeting recordings (auto-transcribed), shared docs, onboarding |
| **Apple Notes** | Quick capture | iPhone and Mac quick notes — exported nightly to Obsidian Brain |

---

## Communication

| Tool | Role | Why |
|------|------|-----|
| **Slack** | Team communication | Channels for dev (#dev), general, customers. Webhooks from GitHub, Linear, Vercel. |
| **Notion** | Async documentation | Meeting notes, decisions, SOPs. Linked from Slack threads. |

---

## Growth & Outreach

| Tool | Role | Why |
|------|------|-----|
| **LinkedIn Premium + Sales Navigator** | B2B outreach | Investor and enterprise customer pipeline. Sales Nav for advanced search filters. |
| **Dripify** | LinkedIn automation | Automated connection sequences, message drip campaigns for investor/customer outreach |
| **Instagram (verified)** | Brand presence | Personal brand and Airbank presence |
| **ManyChat** | Social media automation | Automated DM flows, lead capture from social |

---

## Design

| Tool | Role | Why |
|------|------|-----|
| **Framer** | Marketing website | No-code/low-code frontend for airbank.ca marketing site |
| **shadcn/ui** | Product UI | Every component in every product. Consistent, accessible, composable. |

---

## Finance & Operations

| Tool | Role | Why |
|------|------|-----|
| **QuickBooks** | Accounting | Invoicing, expense tracking, financial reporting |
| **Venn** | Business banking | Digital corporate cards, online business account, expense management |

---

## Infrastructure

| Tool | Role | Why |
|------|------|-----|
| **Google Cloud Platform** | Cloud infrastructure | Vertex AI, Cloud Storage, project management |
| **Supabase** | Database + auth | PostgreSQL, row-level security, auth, file storage. One project across all Airbank products. |
| **Proxmox** | Bare-metal hypervisor | 2-node home server cluster running all self-hosted services |
| **Docker** | Containerisation | All homelab services and AI agents in containers |
| **Tailscale** | VPN mesh | Zero-config secure access to homelab from any device, anywhere |

---

## Tool Decision Principles

1. **AI-first always** — if a tool doesn't have AI or an API, there's probably a better option
2. **Integrate everything** — Slack receives events from GitHub, Vercel, Linear. Nothing is siloed.
3. **Automate the boring parts** — outreach sequences, vault sync, git exports, deploy pipeline
4. **Own your data** — critical knowledge lives in Obsidian (local + iCloud), not in a vendor's database
5. **shadcn/ui for all UI** — universal rule, no exceptions, across every project
