# Airbank — Platform Stack

> AI-native M&A platform. Automates Quality of Earnings for lower middle market deals.
> QoE traditionally costs $25k–$250k and takes 6 weeks. Airbank does it in 48 hours, one click.

---

## Products

### Quality of Earnings
AI-powered QoE workbook compressing weeks of financial analysis into minutes.

- Upload financial documents (PDFs, Excel, GL exports)
- RAG-grounded extraction across 11 report sections — every cell cites source, page, excerpt
- Confidence scores on every AI-extracted value
- AI-generated flags for low-confidence data, discrepancies, anomalies
- Full audit trail for every cell edit
- Export to Excel, Google Sheets, or PDF

**11 QoE sections:**
Income Statement · Quality of Earnings (EBITDA bridge) · Margins by Month · Balance Sheet ·
Working Capital · Net Debt · Sales by Channel · Customer Concentration ·
Proof of Revenue · Proof of Cash · Risk & Diligence

### Data Room
AI-augmented document collection and analysis.

- Drag-and-drop folder uploads (preserves full folder hierarchy)
- AI diligence checklist builder — describe what you need, AI generates structured requirements
- Request data from counterparty with checklist attached
- AI chat scoped to the data room — ask questions about what's uploaded, what's missing
- List, grid, and compact view modes

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router) + React 19 + TypeScript |
| Styling | Tailwind CSS v4 + shadcn/ui |
| Database | Supabase PostgreSQL + Row Level Security |
| Auth | Supabase Auth via `@supabase/ssr` (cookie sessions) |
| File Storage | Supabase Storage (`qoe-documents` bucket, private) |
| Document Storage | Google Cloud Storage (`qoe-rag-documents` bucket) |
| AI / Extraction | Gemini 3 Flash via Vertex AI |
| RAG Engine | Vertex AI RAG API (one corpus per workbook) |
| AI Chat | Anthropic Claude + Gemini (model-selectable) |
| Charts | Recharts |
| Export | SheetJS (xlsx) + Google Sheets API |
| Deployment | Vercel |

---

## Architecture

```
Browser → Next.js App Router (Vercel Edge)
              │
    ┌─────────┼──────────────┐
    ▼         ▼              ▼
Supabase   Vertex AI     Google Cloud
(DB/Auth/  (Gemini 3   Storage
 Storage)   + RAG)       (Documents)
```

**QoE Analysis flow:**
```
1. Upload documents  →  Supabase Storage  →  GCS  →  RAG corpus import
2. Trigger analysis  →  SSE stream opens (11 sections, max 5 min)
3. Per section:      →  RAG query  →  Gemini extraction  →  cells + flags → DB
4. Completion        →  workbook fetches all cells, renders interactive report
```

**Data Room flow:**
```
1. Create company    →  POST /api/workbooks (type: 'company')
2. Upload files      →  Supabase Storage + GCS (folder structure preserved)
3. AI chat           →  answers questions using file listing as context
```

---

## Infrastructure

| Resource | Value |
|----------|-------|
| Supabase project | `qlhdslbpgnctshcpiqfv` |
| GCS bucket | `qoe-rag-documents` |
| Supabase Storage | `qoe-documents` (private) |
| GCP project | `nodebase-473513` |
| GCP location | `us-central1` |
| Gemini model | `gemini-3` |
| Deployment | Vercel (auto-deploy on push to `main`) |

---

## Database Schema

```sql
workbooks           -- one per engagement or data room
documents           -- uploaded file metadata
rag_corpora         -- one RAG corpus per QoE workbook
workbook_cells      -- extracted cells (section, row_key, period, value, confidence)
cell_flags          -- AI-generated or manual flags on cells
flag_comments       -- threaded comments per flag
audit_entries       -- edit history for cell overrides
missing_data_requests -- AI-identified data gaps
```

All tables have Row Level Security (RLS) enabled.

---

## Key Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| Next.js 16 App Router | Server components + streaming for SSE analysis |
| `proxy.ts` not `middleware.ts` | Next.js 16 renamed middleware — creating both causes build error |
| Vertex AI RAG (not LangChain) | Native GCP integration, no abstraction layer, lower latency |
| One Supabase project across all products | Shared auth, shared storage, single DB to manage |
| Gemini 3 Flash (not Pro) | Flash is available in this GCP project + faster for extraction |
| SSE for analysis stream | Real-time progress for a 5-minute operation — better UX than polling |
| Demo bypass (`/^\d$/.test(id)`) | Demo workbooks (IDs 1–5) bypass API — no auth required for demo |

---

## API Surface

```
POST   /api/auth                           signup + login
GET    /api/workbooks                      list workbooks
POST   /api/workbooks                      create workbook
GET    /api/workbooks/[id]/analyze         SSE analysis stream (11 sections)
GET    /api/workbooks/[id]/cells           cells with source + flags
PATCH  /api/workbooks/[id]/cells/[cellId]  save cell override + audit entry
GET    /api/workbooks/[id]/flags           list all flags
POST   /api/workbooks/[id]/flags           create manual flag
PATCH  /api/workbooks/[id]/flags/[flagId]  resolve / update flag
GET    /api/workbooks/[id]/flags/[flagId]/comments   flag comments
POST   /api/workbooks/[id]/flags/[flagId]/comments   add comment
POST   /api/workbooks/[id]/documents       upload document
POST   /api/workbooks/[id]/export          export (excel / sheets / pdf)
GET    /api/workbooks/[id]/audit           audit log
GET    /api/chat                           AI chat (Claude + Gemini)
```

---

## Live Demo

**URL:** https://airbank-platform.vercel.app
**Login:** `user@test.com` / `TestPass123!`

Explore Alpine Outdoor Co. — a realistic mock engagement with 3 years of financials,
a pre-built data room, and a live QoE workbook.

---

## Roadmap

The QoE workbook is the wedge into automating the entire M&A deal lifecycle:

| Phase | Products |
|-------|---------|
| **Now** | Data Room · Quality of Earnings |
| **Next** | Working Capital Peg · Legal DD · Management Q&A |
| **Then** | SPA Issues Tracker · CIM Analyzer · Purchase Price Waterfall |
| **Vision** | Full LOI-to-close on one platform — 30 days, 20% of traditional advisory cost |
