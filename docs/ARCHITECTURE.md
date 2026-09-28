# CarVal Architecture

## Overview

CarVal is a multi-phase vehicle inspection platform. The architecture supports progressive enhancement from Review 2 (core Vision & Document AI) through Review 4 (LLM synthesis and evidence-backed reports).

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│              (Dashboard, Upload, Results UI)                │
└────────────┬────────────────────────────────────────────────┘
             │ HTTP/REST
┌────────────▼────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│              (Orchestration, File Handling)                 │
├─────────────┬──────────────────┬──────────────┬─────────────┤
│             │                  │              │             │
│  Health     │  Inspection API  │  File Mgmt   │   Utils     │
│  Check      │                  │              │             │
└─────┬───────┴────┬─────────────┴────┬─────────┴─────────────┘
      │            │                  │
      │      ┌─────▼──────────────────┴──────────────┐
      │      │   Service Integration Layer           │
      │      └────┬─────────────────┬──────────────┬─┘
      │           │                 │              │
  ┌───▼───┐  ┌────▼────┐    ┌──────▼───┐   ┌─────▼──────┐
  │Health │  │ Vision  │    │Document  │   │ Valuation  │
  │Check  │  │Service  │    │ AI       │   │(Review 3+) │
  │       │  │(Member1)│    │(Member2) │   │            │
  └───────┘  └─────────┘    └──────────┘   └────────────┘

   │                         │                 │
   │                         │                 │
  ┌▼──────────────────────────▼─────────────────▼──────────────┐
  │                   Common Data Contract                      │
  │            (CarVal Vehicle JSON Schema v1.0)               │
  │  vehicle | vision | documents | vehicle_history |          │
  │  valuation | discrepancies | rag | llm | report            │
  └────────────────────────────────────────────────────────────┘
```

## Data Flow (Review 2)

```
1. USER UPLOADS
   ├─ Car Images (JPG, PNG)
   └─ Vehicle Documents (PDF, images)
            │
            ▼
2. BACKEND RECEIVES
   ├─ Creates Inspection ID
   ├─ Stores file metadata
   └─ Orchestrates services
            │
            ├─────────────────┬─────────────────┐
            ▼                 ▼                 ▼
3. PARALLEL PROCESSING
   │
   ├─ VISION SERVICE (Member 1)
   │  ├─ YOLOv8 Inference
   │  ├─ Damage Detection
   │  └─ Returns: damages, confidence, bounding boxes
   │
   └─ DOCUMENT AI (Member 2)
      ├─ OCR Processing
      ├─ Field Extraction
      └─ Returns: RC info, insurance data, service history
            │
            ▼
4. BACKEND AGGREGATES
   └─ Merges results into Vehicle JSON
            │
            ▼
5. FRONTEND DISPLAYS
   ├─ Dashboard with results
   ├─ Damage visualization (bounding boxes)
   ├─ Extracted document info
   └─ Combined vehicle summary
```

## Technology Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Frontend** | Next.js + TypeScript | React SSR, API client, UI components |
| **Backend** | FastAPI + Python | REST API, file handling, orchestration |
| **Vision** | YOLOv8 + Python | Object detection, damage classification |
| **Document AI** | OCR + Python | Text extraction, field parsing |
| **Data** | JSON Schema | Versioned, extensible, backward-compatible |
| **Storage** | Local JSON + SQLite | Review 2: JSON; Review 3+: Database |

## API Endpoints (Review 2)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Service status |
| `POST` | `/inspection` | Create new inspection |
| `POST` | `/inspection/{id}/images` | Upload car images |
| `POST` | `/inspection/{id}/documents` | Upload documents |
| `POST` | `/inspection/{id}/vision` | Trigger vision analysis |
| `POST` | `/inspection/{id}/documents/extract` | Trigger document extraction |
| `GET` | `/inspection/{id}` | Get combined results (Vehicle JSON) |

## Modules & Ownership

| Member | Module | Responsibility |
|--------|--------|-----------------|
| **1** | Vision | YOLOv8 damage detection, inference API |
| **2** | Document AI | OCR, field extraction, document API |
| **3** | Frontend + Backend | Next.js dashboard, FastAPI orchestrator |
| **4** | Testing + Support | Test cases, integration, documentation |

## Review Roadmap

### Review 2 (Current)
- ✅ Vision Service + inference
- ✅ Document AI extraction
- ✅ FastAPI orchestration
- ✅ Next.js frontend
- ✅ Combined Vehicle JSON

### Review 3
- Valuation Service (XGBoost)
- Discrepancy Detection
- Hybrid RAG Layer
- Database integration

### Review 4
- LLM Synthesis (GPT-4 / Claude)
- Evidence-backed Report
- Negotiation Insights
- Final Buyer Report

## Development Strategy

1. **Week 1**: Repository setup, schema agreement, skeleton services
2. **Week 2**: Real Vision/Document AI integration, end-to-end demo
3. **Review 2 Demo**: Functional prototype with all core features working

## Important Principles

- **Data Contract First**: All modules agree on `vehicle_schema_v1.json`
- **Traceability**: Every finding (damage, extraction) references source (image ID, document ID)
- **Backward Compatibility**: New fields are added, never remove or rename existing ones
- **Environment-Based Config**: Secrets and URLs from `.env`, never in code
- **Incremental Integration**: Use mock responses while services are being built
