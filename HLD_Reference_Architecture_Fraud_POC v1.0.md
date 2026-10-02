# High-Level Design (HLD) / Reference Architecture
### Fraud Detection & Resolution Automation — BFSI POC

---

| Field | Details |
|---|---|
| **Document Version** | v1.0 |
| **Prepared By** | Aditya Singh |
| **Organisation** | Self Learning |
| **Date** | October 2026 |
| **Status** | Draft |
| **Refers To** | Business Case v1.0 ✅ | HLR/BRD v1.0 ✅ |
| **Classification** | Internal / Confidential |

---

## 1. DOCUMENT PURPOSE

This document describes the **High-Level Design (HLD)** and **Reference Architecture** for the Fraud Detection & Resolution Automation POC. It defines:
- The overall solution architecture and component layout
- How data flows through the system
- Integration approach with existing enterprise systems
- Security, governance, and deployment model
- Technology choices at a conceptual level

> **Audience:** Solution Architect, Full Stack Developer, IT/Cloud Architect, QA Lead
> **Does NOT cover:** Detailed API specs, DB schemas, code logic — those go in the LLD.

---

## 2. ARCHITECTURE PRINCIPLES

| # | Principle | Rationale |
|---|---|---|
| 1 | **AI-Augmented, Human-Controlled** | All autonomous decisions are bounded by business rules; humans retain override authority |
| 2 | **Loosely Coupled** | Each component interacts via APIs/events; replacing any layer doesn't break others |
| 3 | **Security by Design** | Encryption, RBAC, and audit logging built in from Day 1, not added later |
| 4 | **Explainability First** | Every AI decision must produce a human-readable rationale — non-negotiable for BFSI |
| 5 | **Cloud-Native, POC-Scoped** | Deploy on managed cloud services to minimise infra overhead during POC |
| 6 | **Data Minimisation** | Only the data needed for fraud triage enters the platform; no bulk data migration |

---

## 3. REFERENCE ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │   Analyst Dashboard  │    │  Compliance Report Portal    │   │
│  │  (Case Queue / UI)   │    │  (PDF / CSV Export)          │   │
│  └──────────┬───────────┘    └──────────────┬───────────────┘   │
└─────────────┼────────────────────────────────┼───────────────────┘
              │ REST API                        │ REST API
┌─────────────▼────────────────────────────────▼───────────────────┐
│                     ORCHESTRATION LAYER                           │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │               AI Agent Orchestrator                      │    │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│   │  │  Triage      │  │  Resolution  │  │  Escalation  │  │    │
│   │  │  Agent       │  │  Agent       │  │  Agent       │  │    │
│   │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│   │  ┌──────────────┐  ┌──────────────┐                     │    │
│   │  │  Report      │  │  Query       │                     │    │
│   │  │  Agent       │  │  Agent (C2A) │                     │    │
│   │  └──────────────┘  └──────────────┘                     │    │
│   └─────────────────────────────────────────────────────────┘    │
│                         │            │                            │
│              ┌───────────┘            └──────────────┐           │
│              ▼                                        ▼           │
│   ┌─────────────────────┐             ┌───────────────────────┐  │
│   │   KNOWLEDGE LAYER   │             │   GOVERNANCE LAYER    │  │
│   │  (RAG Engine)       │             │   (AI Guard / Rules)  │  │
│   │  - Fraud policies   │             │   - 30+ rule checks   │  │
│   │  - Past case data   │             │   - Audit log writer  │  │
│   │  - Customer context │             │   - Explainability    │  │
│   └─────────────────────┘             └───────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
              │ Secure API / Event Stream
┌─────────────▼───────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                           │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              Enterprise Connector (Adapter)               │  │
│   │         [FILL: Source Fraud Alert System Name]            │  │
│   └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                    ENTERPRISE SYSTEMS (Existing)                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │  Core Fraud  │  │   Core       │  │   Policy / Document  │  │
│   │  Alert System│  │   Banking /  │  │   Repository         │  │
│   │  [FILL]      │  │   CRM [FILL] │  │   [FILL]             │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                      DATA & STORAGE LAYER                        │
│   ┌────────────────┐  ┌──────────────────┐  ┌───────────────┐   │
│   │  Vector Store  │  │  Case / Audit DB │  │  Report Store │   │
│   │  (RAG index)   │  │  (immutable log) │  │  (PDF/CSV)    │   │
│   └────────────────┘  └──────────────────┘  └───────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 4. LAYER-BY-LAYER BREAKDOWN

### 4a. Presentation Layer

| Component | Description | Users |
|---|---|---|
| **Analyst Dashboard** | Web UI — shows live alert queue, case details, AI recommendation, override controls | Fraud Analysts |
| **Manager View** | Sub-view of dashboard — KPI metrics, team throughput, auto-resolution rate | Fraud Ops Manager |
| **Compliance Report Portal** | Generates, previews, and exports daily/weekly reports in PDF and CSV | Compliance Officer |

**Key Design Decisions:**
- Web-based only (no mobile for POC)
- Role-based access control (RBAC) — analysts see only their queue
- Single-page application (SPA) for real-time alert updates without page refresh

---

### 4b. Orchestration Layer — AI Agents

| Agent | Responsibility | Triggers |
|---|---|---|
| **Triage Agent** | Ingests alert → applies AI reasoning → classifies as High / Medium / Low risk | New alert received from integration layer |
| **Resolution Agent** | Autonomously resolves Low-risk false positives; writes resolution record | Triage Agent outputs Low-risk classification |
| **Escalation Agent** | Builds case summary (customer profile + risk indicators + recommendation) → pushes to analyst queue | Triage Agent outputs Medium/High-risk |
| **Report Agent** | Pulls daily case data → generates compliance report → stores to Report Store | Scheduled trigger (daily 07:45 AM) |
| **Query Agent (C2A)** | Natural language query interface — analysts ask questions, agent retrieves case data | Analyst query via dashboard chat input |

**Agent Collaboration Flow:**
```
Alert In → Triage Agent
              │
        ┌─────┴─────────┐
      Low Risk       Med/High Risk
        │                  │
  Resolution Agent    Escalation Agent
        │                  │
  Auto-Close          Analyst Queue
  + Audit Log         + Case Summary
                           │
                     Analyst Reviews
                     (Accept/Modify/Reject)
                           │
                      Audit Log
```

---

### 4c. Knowledge Layer (RAG Engine)

The **Retrieval-Augmented Generation (RAG)** engine gives agents contextual intelligence grounded in the organisation's own data — preventing hallucination and ensuring decisions are policy-aligned.

| Knowledge Source | Content | Ingestion Method |
|---|---|---|
| Fraud policy documents | Internal fraud rules, thresholds, regulatory guidelines | File upload (PDF/DOCX) → vectorised |
| Historical fraud cases | Past case decisions and outcomes (anonymised) | Batch import → vectorised |
| Customer context | 90-day transaction history snapshot (anonymised) | API pull at query time |

**Vector Store:** Stores embeddings of all knowledge documents. Agents query the vector store at runtime to retrieve the most relevant policy excerpts and past case patterns before making a decision.

---

### 4d. Governance Layer

The Governance Layer acts as an **always-on guardrail** — every agent action passes through it before execution.

| Governance Check | What It Validates |
|---|---|
| **Business Rule Engine** | Enforces BR-01 to BR-06 (e.g., no auto-resolve above ₹X threshold) |
| **Explainability Module** | Attaches human-readable rationale to every AI decision |
| **Audit Log Writer** | Immutably records: timestamp, agent ID, input data, decision, confidence score, rule checks passed/failed |
| **Anomaly Detector** | Flags if auto-resolution rate drops below 30% → alerts Fraud Ops Manager |
| **Data Masking** | Ensures no PII leaves the governance boundary in logs or reports |

---

### 4e. Integration Layer

**Connector Design (POC scope: 1 system):**

```
Source System → Webhook / API Push → Connector Adapter → Event Queue → Triage Agent
```

| Design Choice | Detail |
|---|---|
| **Integration pattern** | Event-driven (webhook or polling — to be confirmed with IT) |
| **Protocol** | REST over HTTPS (TLS 1.2+) |
| **Auth** | OAuth 2.0 / API Key (to be confirmed with source system team) |
| **Payload format** | JSON |
| **Error handling** | Failed ingestion retried 3× with exponential backoff; dead-letter queue for persistent failures |
| **Impact on source** | Read-only access; no write-back to source system during POC |

---

### 4f. Data & Storage Layer

| Store | Technology (Placeholder) | Data Held | Retention |
|---|---|---|---|
| **Vector Store** | `[FILL: e.g., managed vector DB service]` | Knowledge embeddings (policy + history) | Duration of POC |
| **Case & Audit DB** | `[FILL: e.g., managed relational or NoSQL DB]` | Case records, audit logs — immutable | `[FILL: 7 years per regulation]` |
| **Report Store** | Cloud object storage | Generated PDF/CSV compliance reports | `[FILL: per policy]` |

---

## 5. DATA FLOW (End-to-End)

```
Step 1 → Fraud alert generated in source system
Step 2 → Connector picks up alert (webhook / polling)
Step 3 → Governance Layer: validate alert schema + business rule pre-check
Step 4 → Triage Agent: RAG query (fetch relevant policy + customer context)
Step 5 → Triage Agent: LLM reasoning → classify alert (High/Med/Low) + generate rationale
Step 6 → Governance Layer: post-decision audit log written
         ├── If LOW RISK → Resolution Agent → auto-close → audit record stored
         └── If MED/HIGH → Escalation Agent → build case summary → push to analyst queue
Step 7 → Analyst reviews case (accept / modify / reject AI recommendation)
Step 8 → Analyst action recorded in audit log
Step 9 → Report Agent (daily) → pulls all case data → generates compliance report → stored
```

---

## 6. SECURITY ARCHITECTURE

| Layer | Security Control |
|---|---|
| **Network** | All traffic over TLS 1.2+; no public endpoints for internal services |
| **Authentication** | Single Sign-On (SSO) via `[FILL: Azure AD / existing IdP]`; MFA enforced |
| **Authorisation** | Role-Based Access Control (RBAC) — Analyst / Manager / Compliance / Admin roles |
| **Data in transit** | TLS 1.2+ encrypted for all API calls |
| **Data at rest** | AES-256 encryption for all storage (Vector Store, Case DB, Report Store) |
| **Data masking** | PII masked in all logs, reports, and UI displays (last 4 digits of account only) |
| **Audit trail** | Immutable audit log — write-once, append-only; accessible to Compliance role only |
| **Secrets management** | API keys and credentials stored in managed secrets vault (not in code) |
| **Penetration testing** | Not required for POC; required before production rollout |

---

## 7. DEPLOYMENT ARCHITECTURE (POC)

```
┌─────────────────────── Cloud Environment (POC) ─────────────────┐
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  Virtual Network (VNet)                     │  │
│  │                                                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │  AI Platform │  │  Web App     │  │  Data Services   │  │  │
│  │  │  (Agents +   │  │  (Dashboard  │  │  (Vector Store + │  │  │
│  │  │  RAG + Gov.) │  │  + Reports)  │  │  Case DB)        │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │          Monitoring & Logging Service                 │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          │ Private Link / VPN                     │
└──────────────────────────┼────────────────────────────────────────┘
                           │
              ┌────────────▼─────────────┐
              │  On-Premises / Existing  │
              │  Enterprise Systems      │
              │  [FILL: Source system]   │
              └──────────────────────────┘
```

| Decision | Choice | Rationale |
|---|---|---|
| **Deployment target** | Cloud (managed services) | Fast POC setup; no infra procurement |
| **Connectivity to on-prem** | Private Link / Site-to-Site VPN | Secure; no data traverses public internet |
| **Environment isolation** | Separate POC subscription/account | No risk to production workloads |
| **GPU compute** | Managed GPU instances (if needed for LLM inference) | Provisioned on demand for POC |

---

## 8. TECHNOLOGY STACK (POC — Placeholder)

> Note: Final technology selections will be confirmed in the Low-Level Design (LLD). Below are reference choices to be validated.

| Layer | Component | Placeholder Technology |
|---|---|---|
| AI Orchestration | Agent framework | `[FILL: as per platform capability]` |
| LLM / Inference | Foundation model | `[FILL: to be confirmed — e.g., GPT-4o, Llama 3, Gemini]` |
| RAG / Vector DB | Knowledge retrieval | `[FILL: e.g., Azure AI Search, Pinecone, pgvector]` |
| Backend API | Agent → UI communication | REST API / Python FastAPI |
| Frontend UI | Analyst Dashboard | React.js / Next.js |
| Database | Case & Audit records | `[FILL: PostgreSQL / Cosmos DB]` |
| Storage | Report Store | Cloud Blob / Object Storage |
| Auth | Identity | `[FILL: Azure AD / Okta / existing IdP]` |
| Secrets | Credential mgmt | Managed Secrets Vault |
| Monitoring | Logs + alerts | `[FILL: Cloud-native monitoring service]` |
| CI/CD (POC) | Deployment pipeline | `[FILL: GitHub Actions / Azure DevOps]` |

---

## 9. KEY DESIGN DECISIONS & RATIONALE

| # | Decision | Chosen Approach | Rejected Alternative | Why |
|---|---|---|---|---|
| 1 | Integration pattern | Event-driven (webhook) | Batch file transfer | Real-time alerting requirement (FR-01) |
| 2 | Data usage in POC | Anonymised / synthetic | Real production data | Data privacy, regulatory compliance (NFR-06) |
| 3 | Deployment model | Cloud (managed) | On-premises | Speed of POC setup; avoid infra lead time |
| 4 | Agent architecture | Specialised agents per function | Single monolithic agent | Maintainability, testability, single responsibility principle |
| 5 | Knowledge layer | RAG-based | Fine-tuning only | RAG allows real-time policy updates without model retraining |
| 6 | Auto-resolve scope | Low-risk only + value threshold | All low-risk | Business Rule BR-01; risk mitigation |

---

## 10. RISKS & DESIGN MITIGATIONS

| Risk | Design Mitigation |
|---|---|
| AI hallucinates incorrect fraud decision | RAG grounds every decision in policy docs; Governance Layer validates before action |
| Source system API unavailable | Retry logic + dead-letter queue; POC can switch to file-based batch if needed |
| LLM latency causes slow triage | NFR-01 (≤ 30 sec) monitored via cloud metrics; GPU compute provisioned if needed |
| Audit log tampered | Write-once, append-only DB with access restricted to Compliance role |
| Integration breaks source system | Read-only connector; load tested before pilot week |

---

## 11. OUT OF SCOPE (Architecture)

- Multi-region / disaster recovery architecture (not required for POC)
- High-availability failover design (POC availability target: 99%)
- Mobile or native app UI
- Fine-tuning or training of any AI/ML model
- Write-back / action on source systems (e.g., card freeze)

---

## 12. NEXT STEPS

| # | Action | Owner | Sequence |
|---|---|---|---|
| 1 | HLD review & sign-off by IT Architect + Compliance | IT Architect, Legal | Now |
| 2 | Begin **Low-Level Design (LLD)** — API specs, DB schema, agent workflow detail | FSD (Aditya Singh) | After HLD sign-off |
| 3 | Begin **UX / UI Design** — wireframes & prototypes | UX Designer | Parallel to LLD |
| 4 | Confirm source system API specs with IT | IT + Source System Team | Now |
| 5 | Confirm LLM / vector DB technology selection | Architect + FSD | During LLD |

---

*Document Owner: Aditya Singh | Version: 1.0 | Date: October 2026*
*This is a learning exercise document. All technology references are placeholders to be confirmed in LLD.*
