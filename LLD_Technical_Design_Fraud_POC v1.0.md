# Low-Level Design (LLD) / Technical Design Document
### Fraud Detection & Resolution Automation — BFSI POC

---

| Field | Details |
|---|---|
| **Document Version** | v1.0 |
| **Prepared By** | Aditya Singh |
| **Organisation** | Self Learning |
| **Date** | October 2026 |
| **Status** | Draft |
| **Refers To** | Business Case v1.0 ✅ · HLR/BRD v1.0 ✅ · HLD v1.0 ✅ |
| **Classification** | Internal / Confidential |

---

## 1. PURPOSE

This document provides the **detailed technical design** for every component described in the HLD. It is the primary reference for the development team during the POC build phase. It defines:
- API contracts (request/response schemas)
- Database schemas and data models
- Agent workflow logic (pseudocode level)
- RAG pipeline internals
- Governance rule engine design
- Error handling and retry strategy
- Environment configuration
- CI/CD pipeline design
- Test case mapping to requirements

---

## 2. SYSTEM COMPONENT MAP

```
┌──────────────────────────────────────────────────────────────┐
│  Component            │ Tech (Placeholder)   │ Owner         │
│─────────────────────────────────────────────────────────────│
│  Connector Service    │ Python / FastAPI      │ FSD           │
│  Event Queue          │ Managed Message Queue │ FSD + Infra   │
│  Triage Agent         │ Python + LLM SDK      │ FSD           │
│  Resolution Agent     │ Python + LLM SDK      │ FSD           │
│  Escalation Agent     │ Python + LLM SDK      │ FSD           │
│  Report Agent         │ Python + Scheduler    │ FSD           │
│  Query Agent (C2A)    │ Python + LLM SDK      │ FSD           │
│  RAG Engine           │ Vector DB + Embeddings│ FSD           │
│  Governance Module    │ Python (rule engine)  │ FSD           │
│  Case & Audit DB      │ PostgreSQL            │ FSD + DBA     │
│  Vector Store         │ [FILL: pgvector/etc.] │ FSD           │
│  Report Store         │ Cloud Blob Storage    │ Infra         │
│  Analyst Dashboard    │ React.js / Next.js    │ FSD + UX      │
│  Auth Service         │ [FILL: existing IdP]  │ IT            │
│  Secrets Vault        │ Managed Secrets Svc   │ Infra         │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. API CONTRACTS

### 3a. Connector Service — Ingest Alert

**Endpoint:** `POST /api/v1/alerts/ingest`
**Caller:** Source fraud alert system (webhook push)
**Auth:** API Key (header: `X-API-Key`)

**Request Body:**
```json
{
  "alert_id": "string (UUID)",
  "source_system": "string",
  "generated_at": "ISO8601 datetime",
  "transaction": {
    "txn_id": "string",
    "amount": "number",
    "currency": "string (ISO 4217)",
    "channel": "string (e.g., ATM, NEFT, UPI)",
    "merchant_id": "string | null",
    "timestamp": "ISO8601 datetime"
  },
  "account": {
    "account_ref": "string (masked — last 4 digits only)",
    "customer_ref": "string (anonymised ID)",
    "customer_tier": "string (STANDARD | PRIORITY | VIP)"
  },
  "alert_type": "string (e.g., VELOCITY_BREACH, GEO_ANOMALY, CNP_FRAUD)",
  "raw_score": "number (0.0–1.0, from source system)",
  "metadata": "object | null"
}
```

**Response — 202 Accepted:**
```json
{
  "status": "ACCEPTED",
  "internal_case_id": "string (UUID)",
  "received_at": "ISO8601 datetime",
  "message": "Alert queued for triage"
}
```

**Response — 400 Bad Request:**
```json
{
  "status": "ERROR",
  "code": "INVALID_PAYLOAD",
  "message": "string describing validation failure"
}
```

---

### 3b. Analyst Dashboard — Get Case Queue

**Endpoint:** `GET /api/v1/cases`
**Caller:** Analyst Dashboard (frontend)
**Auth:** Bearer token (SSO)
**Query Params:** `status`, `risk_level`, `assigned_to`, `page`, `page_size`

**Response — 200 OK:**
```json
{
  "total": "integer",
  "page": "integer",
  "page_size": "integer",
  "cases": [
    {
      "case_id": "string (UUID)",
      "alert_id": "string",
      "risk_level": "HIGH | MEDIUM | LOW",
      "status": "OPEN | AUTO_RESOLVED | ESCALATED | CLOSED",
      "ai_recommendation": "string",
      "ai_rationale": "string",
      "confidence_score": "number (0.0–1.0)",
      "transaction_amount": "number",
      "currency": "string",
      "created_at": "ISO8601 datetime",
      "assigned_to": "string (analyst_id) | null"
    }
  ]
}
```

---

### 3c. Analyst Dashboard — Submit Decision

**Endpoint:** `POST /api/v1/cases/{case_id}/decision`
**Caller:** Analyst Dashboard
**Auth:** Bearer token (SSO)

**Request Body:**
```json
{
  "decision": "ACCEPT | MODIFY | REJECT",
  "final_action": "CLOSE_FALSE_POSITIVE | ESCALATE_TO_INVESTIGATION | BLOCK_ACCOUNT | OTHER",
  "analyst_notes": "string | null",
  "modified_risk_level": "HIGH | MEDIUM | LOW | null"
}
```

**Response — 200 OK:**
```json
{
  "status": "DECISION_RECORDED",
  "case_id": "string",
  "decided_by": "string (analyst_id)",
  "decided_at": "ISO8601 datetime",
  "audit_log_id": "string (UUID)"
}
```

---

### 3d. Query Agent (C2A) — Natural Language Query

**Endpoint:** `POST /api/v1/query`
**Caller:** Analyst Dashboard chat input
**Auth:** Bearer token (SSO)

**Request Body:**
```json
{
  "query": "string (natural language, max 500 chars)",
  "context": {
    "analyst_id": "string",
    "session_id": "string"
  }
}
```

**Response — 200 OK:**
```json
{
  "query_id": "string (UUID)",
  "answer": "string (natural language response)",
  "supporting_data": "object | null",
  "sources": ["string (document or DB references)"],
  "response_time_ms": "integer"
}
```

---

### 3e. Report Agent — Trigger / Get Report

**Endpoint:** `GET /api/v1/reports/daily?date=YYYY-MM-DD`
**Caller:** Compliance Portal or scheduled job
**Auth:** Bearer token (Compliance role required)

**Response — 200 OK:**
```json
{
  "report_id": "string (UUID)",
  "report_date": "YYYY-MM-DD",
  "generated_at": "ISO8601 datetime",
  "summary": {
    "total_alerts": "integer",
    "auto_resolved": "integer",
    "escalated": "integer",
    "analyst_closed": "integer",
    "avg_resolution_time_hrs": "number",
    "auto_resolution_rate_pct": "number"
  },
  "download_url": "string (pre-signed URL, expires in 1 hour)"
}
```

---

## 4. DATABASE SCHEMAS

### 4a. Cases Table (`cases`)

```sql
CREATE TABLE cases (
    case_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id            VARCHAR(255) NOT NULL UNIQUE,
    source_system       VARCHAR(100) NOT NULL,
    internal_ref        VARCHAR(255),

    -- Transaction (masked / anonymised)
    txn_id              VARCHAR(255) NOT NULL,
    txn_amount          NUMERIC(18, 2) NOT NULL,
    txn_currency        CHAR(3) NOT NULL,
    txn_channel         VARCHAR(50),
    txn_timestamp       TIMESTAMPTZ NOT NULL,

    -- Account (anonymised)
    account_ref         VARCHAR(50) NOT NULL,   -- masked last 4 digits
    customer_ref        VARCHAR(255) NOT NULL,  -- anonymised ID
    customer_tier       VARCHAR(20) NOT NULL DEFAULT 'STANDARD',

    -- AI Decision
    risk_level          VARCHAR(10) CHECK (risk_level IN ('HIGH','MEDIUM','LOW')),
    ai_recommendation   TEXT,
    ai_rationale        TEXT,
    confidence_score    NUMERIC(5,4),

    -- Status & Resolution
    status              VARCHAR(30) NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN','TRIAGE_IN_PROGRESS',
                                          'ESCALATED','AUTO_RESOLVED','CLOSED')),
    final_action        VARCHAR(50),
    resolution_notes    TEXT,
    resolved_by         VARCHAR(255),          -- 'SYSTEM' or analyst_id
    resolved_at         TIMESTAMPTZ,

    -- Timestamps
    alert_received_at   TIMESTAMPTZ NOT NULL,
    triage_completed_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_risk_level ON cases(risk_level);
CREATE INDEX idx_cases_created_at ON cases(created_at);
```

---

### 4b. Audit Log Table (`audit_log`)

```sql
-- Write-once, append-only. No UPDATE or DELETE allowed.
CREATE TABLE audit_log (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id),
    alert_id            VARCHAR(255) NOT NULL,

    -- Actor
    actor_type          VARCHAR(10) NOT NULL CHECK (actor_type IN ('AGENT','ANALYST')),
    actor_id            VARCHAR(255) NOT NULL,  -- agent name or analyst_id
    agent_name          VARCHAR(100),           -- e.g., 'TriageAgent', 'ResolutionAgent'

    -- Action
    action              VARCHAR(100) NOT NULL,
    decision            VARCHAR(100),
    rationale           TEXT,
    confidence_score    NUMERIC(5,4),

    -- Governance
    rules_checked       JSONB,    -- array of rule IDs and pass/fail
    rules_passed        BOOLEAN,
    pii_masked          BOOLEAN NOT NULL DEFAULT TRUE,

    -- Input snapshot (sanitised, no PII)
    input_snapshot      JSONB,

    -- Timestamp
    logged_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent updates and deletes (enforced via DB role permissions)
-- No UPDATE/DELETE grants on audit_log for any application role
CREATE INDEX idx_audit_case_id ON audit_log(case_id);
CREATE INDEX idx_audit_logged_at ON audit_log(logged_at);
```

---

### 4c. Analyst Decisions Table (`analyst_decisions`)

```sql
CREATE TABLE analyst_decisions (
    decision_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id),
    analyst_id          VARCHAR(255) NOT NULL,
    decision            VARCHAR(20) NOT NULL CHECK (decision IN ('ACCEPT','MODIFY','REJECT')),
    final_action        VARCHAR(50) NOT NULL,
    modified_risk_level VARCHAR(10),
    analyst_notes       TEXT,
    decided_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    audit_log_id        UUID REFERENCES audit_log(log_id)
);
```

---

### 4d. Reports Table (`reports`)

```sql
CREATE TABLE reports (
    report_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date         DATE NOT NULL UNIQUE,
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by        VARCHAR(50) NOT NULL DEFAULT 'ReportAgent',
    total_alerts        INTEGER,
    auto_resolved       INTEGER,
    escalated           INTEGER,
    analyst_closed      INTEGER,
    avg_resolution_hrs  NUMERIC(10,2),
    auto_res_rate_pct   NUMERIC(5,2),
    storage_path        TEXT NOT NULL,  -- blob storage path
    download_url        TEXT,           -- pre-signed URL (short-lived)
    status              VARCHAR(20) DEFAULT 'GENERATED'
);
```

---

## 5. AGENT WORKFLOW — DETAILED PSEUDOCODE

### 5a. Triage Agent

```python
class TriageAgent:

    def run(self, alert: AlertPayload) -> TriageResult:

        # Step 1: Pre-check — Governance (business rule pre-validation)
        governance.pre_check(alert)
        # Raises GovernanceViolationError if schema invalid

        # Step 2: Fetch context from RAG engine
        customer_history = rag.query(
            query=f"transaction history for {alert.account.customer_ref}",
            top_k=5
        )
        fraud_policies = rag.query(
            query=f"fraud rules for {alert.alert_type}",
            top_k=3
        )

        # Step 3: Build LLM prompt
        prompt = build_triage_prompt(
            alert=alert,
            customer_history=customer_history,
            fraud_policies=fraud_policies
        )

        # Step 4: Call LLM
        llm_response = llm_client.complete(
            prompt=prompt,
            max_tokens=500,
            temperature=0.1   # Low temp for determinism in fraud decisions
        )

        # Step 5: Parse structured output
        risk_level = parse_risk_level(llm_response)       # HIGH | MEDIUM | LOW
        rationale  = parse_rationale(llm_response)
        confidence = parse_confidence(llm_response)        # 0.0–1.0

        # Step 6: Governance post-check
        governance.post_check(
            case_id=alert.internal_case_id,
            decision=risk_level,
            rationale=rationale,
            rules=TRIAGE_RULES
        )

        # Step 7: Write audit log
        audit_log.write(
            case_id=alert.internal_case_id,
            actor_type="AGENT",
            actor_id="TriageAgent",
            action="TRIAGE_CLASSIFICATION",
            decision=risk_level,
            rationale=rationale,
            confidence_score=confidence
        )

        # Step 8: Route to next agent
        if risk_level == "LOW":
            resolution_agent.run(alert, risk_level, rationale, confidence)
        else:
            escalation_agent.run(alert, risk_level, rationale, confidence)

        return TriageResult(risk_level, rationale, confidence)
```

---

### 5b. Resolution Agent

```python
class ResolutionAgent:

    def run(self, alert, risk_level, rationale, confidence):

        # Business Rule BR-01: Never auto-resolve above value threshold
        if alert.transaction.amount > BUSINESS_RULES["max_auto_resolve_amount"]:
            # Override: escalate despite LOW classification
            audit_log.write(action="AUTO_RESOLVE_OVERRIDDEN_BY_RULE_BR01")
            escalation_agent.run(alert, risk_level, rationale, confidence)
            return

        # Business Rule BR-02: VIP customers always escalate
        if alert.account.customer_tier == "VIP":
            audit_log.write(action="AUTO_RESOLVE_OVERRIDDEN_BY_RULE_BR02")
            escalation_agent.run(alert, risk_level, rationale, confidence)
            return

        # Proceed with auto-resolution
        resolution_record = {
            "case_id":       alert.internal_case_id,
            "status":        "AUTO_RESOLVED",
            "final_action":  "CLOSE_FALSE_POSITIVE",
            "resolved_by":   "SYSTEM",
            "resolved_at":   datetime.utcnow()
        }
        case_db.update(resolution_record)

        # Write audit log
        audit_log.write(
            case_id=alert.internal_case_id,
            actor_type="AGENT",
            actor_id="ResolutionAgent",
            action="AUTO_RESOLVED",
            decision="CLOSE_FALSE_POSITIVE",
            rationale=rationale,
            confidence_score=confidence
        )
```

---

### 5c. Escalation Agent

```python
class EscalationAgent:

    def run(self, alert, risk_level, rationale, confidence):

        # Step 1: Build case summary using RAG
        customer_history = rag.query(
            query=f"full customer profile {alert.account.customer_ref}",
            top_k=10
        )
        similar_cases = rag.query(
            query=f"similar past fraud cases {alert.alert_type}",
            top_k=3
        )

        # Step 2: Generate case summary via LLM
        summary_prompt = build_case_summary_prompt(
            alert=alert,
            risk_level=risk_level,
            customer_history=customer_history,
            similar_cases=similar_cases
        )
        case_summary = llm_client.complete(summary_prompt, max_tokens=800)

        # Step 3: Extract structured recommendation
        recommendation = parse_recommendation(case_summary)

        # Step 4: Update case record
        case_db.update({
            "case_id":           alert.internal_case_id,
            "status":            "ESCALATED",
            "ai_recommendation": recommendation,
            "ai_rationale":      rationale,
            "confidence_score":  confidence
        })

        # Step 5: Push to analyst queue
        analyst_queue.push({
            "case_id":      alert.internal_case_id,
            "risk_level":   risk_level,
            "summary":      case_summary,
            "priority":     map_priority(risk_level)
        })

        # Step 6: Audit log
        audit_log.write(
            actor_id="EscalationAgent",
            action="ESCALATED_TO_ANALYST_QUEUE",
            decision=recommendation
        )
```

---

### 5d. Report Agent (Scheduled — Daily 07:45 AM)

```python
class ReportAgent:

    def run(self, report_date: date):

        # Step 1: Aggregate case data
        stats = case_db.aggregate(
            date=report_date,
            metrics=[
                "total_alerts",
                "auto_resolved_count",
                "escalated_count",
                "analyst_closed_count",
                "avg_resolution_time_hrs",
                "auto_resolution_rate_pct"
            ]
        )

        # Step 2: Generate PDF report
        pdf_bytes = report_renderer.render(
            template="daily_fraud_ops_report.html",
            data=stats,
            date=report_date
        )

        # Step 3: Upload to Report Store
        storage_path = f"reports/{report_date}/fraud_ops_daily.pdf"
        blob_store.upload(path=storage_path, content=pdf_bytes)

        # Step 4: Generate short-lived pre-signed URL
        download_url = blob_store.presign(path=storage_path, expiry_seconds=3600)

        # Step 5: Save report metadata to DB
        reports_db.insert({
            "report_date":       report_date,
            "storage_path":      storage_path,
            "download_url":      download_url,
            **stats
        })

        # Step 6: Anomaly check — alert if auto_res_rate < 30%
        if stats["auto_resolution_rate_pct"] < 30.0:
            notification_service.alert(
                recipient_role="FRAUD_OPS_MANAGER",
                message=f"Auto-resolution rate dropped to {stats['auto_resolution_rate_pct']}% on {report_date}"
            )
```

---

## 6. RAG PIPELINE DESIGN

### 6a. Ingestion Pipeline (One-time + Incremental)

```
Source Documents (PDF/DOCX/CSV)
        │
        ▼
Document Loader → Text Chunker (chunk_size=500, overlap=50)
        │
        ▼
Embedding Model → Generate vector for each chunk
        │
        ▼
Vector Store → Upsert chunks with metadata
        │  Metadata: { doc_type, source_name, ingested_at, chunk_index }
        ▼
Index Ready
```

**Chunking Strategy:**
| Document Type | Chunk Size | Overlap | Rationale |
|---|---|---|---|
| Fraud policy docs | 500 tokens | 50 tokens | Policy clauses are self-contained; small overlap avoids context loss |
| Past case summaries | 300 tokens | 30 tokens | Case records are short; smaller chunks improve precision |
| Customer history | 200 tokens | 0 | Structured tabular data; no overlap needed |

---

### 6b. Query Pipeline (Runtime — per Agent call)

```
Agent sends query string
        │
        ▼
Embedding Model → Generate query vector
        │
        ▼
Vector Store → Similarity search (cosine similarity, top_k=5)
        │
        ▼
Retrieved chunks → Re-ranker (optional, if latency budget allows)
        │
        ▼
Context assembler → Combine chunks into LLM context window
        │
        ▼
LLM Prompt = System prompt + Context + User query
        │
        ▼
LLM Response → Parsed → Returned to Agent
```

---

## 7. GOVERNANCE MODULE — RULE ENGINE

### 7a. Rule Registry

```python
GOVERNANCE_RULES = {
    "BR-01": {
        "description": "No auto-resolve if amount > threshold",
        "check": lambda case: case.txn_amount <= CONFIG["max_auto_resolve_amount"],
        "on_fail": "ESCALATE"
    },
    "BR-02": {
        "description": "VIP customers always escalate",
        "check": lambda case: case.customer_tier != "VIP",
        "on_fail": "ESCALATE"
    },
    "GR-01": {
        "description": "Confidence score must meet minimum threshold",
        "check": lambda result: result.confidence_score >= CONFIG["min_confidence"],
        "on_fail": "ESCALATE"
    },
    "GR-02": {
        "description": "Rationale must be present and non-empty",
        "check": lambda result: bool(result.rationale and len(result.rationale) > 20),
        "on_fail": "REJECT_DECISION"
    },
    "GR-03": {
        "description": "PII must not appear in rationale or audit log",
        "check": lambda result: not pii_detector.scan(result.rationale),
        "on_fail": "MASK_AND_LOG"
    }
}
```

### 7b. Governance Execution Flow

```python
def post_check(case_id, decision, rationale, confidence, rules):
    results = []
    all_passed = True

    for rule_id, rule in rules.items():
        passed = rule["check"](...)
        results.append({"rule_id": rule_id, "passed": passed})
        if not passed:
            all_passed = False
            handle_rule_failure(rule_id, rule["on_fail"], case_id)

    # Always write governance results to audit log
    audit_log.append_governance_result(
        case_id=case_id,
        rules_checked=results,
        rules_passed=all_passed
    )

    return all_passed
```

---

## 8. ERROR HANDLING & RETRY STRATEGY

| Failure Scenario | Handling Strategy | Retry? | Fallback |
|---|---|---|---|
| Source system webhook delivery failure | Source retries (HTTP 202 expected); connector is idempotent on `alert_id` | N/A (source retries) | Dead-letter queue after 3 failures |
| LLM API timeout / error | Exponential backoff: 1s → 2s → 4s (max 3 retries) | Yes — 3× | Escalate to analyst with "AI unavailable" flag |
| LLM returns unparseable output | Retry with simplified prompt once | Yes — 1× | Escalate to analyst with raw LLM output attached |
| Vector store query failure | Retry once; if fails, proceed with LLM without RAG context | Yes — 1× | Log warning; agent runs with reduced context |
| Case DB write failure | Retry 3× with backoff; if persists, alert ops team | Yes — 3× | Alert; do not acknowledge source system webhook |
| Audit log write failure | Critical error — halt agent action; alert immediately | Yes — 3× | Block case progression until audit log write succeeds |
| Report generation failure | Retry once; if fails, alert Compliance Officer | Yes — 1× | Manual report fallback trigger available |

> [!IMPORTANT]
> **Audit log write failures are treated as critical blockers.** No agent action proceeds without a successful audit log entry. This is non-negotiable for BFSI compliance.

---

## 9. CONNECTOR SERVICE — DETAILED DESIGN

```
┌─────────────────────────────────────────────────────────┐
│                   Connector Service                      │
│                                                         │
│  POST /api/v1/alerts/ingest                             │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────┐                               │
│  │  Schema Validator    │ ← Pydantic model validation   │
│  └──────────┬──────────┘                               │
│             │ Valid                                     │
│             ▼                                           │
│  ┌─────────────────────┐                               │
│  │  Idempotency Check   │ ← Check alert_id in DB       │
│  │  (deduplicate)       │   Return 202 if duplicate     │
│  └──────────┬──────────┘                               │
│             │ New alert                                 │
│             ▼                                           │
│  ┌─────────────────────┐                               │
│  │  PII Masker          │ ← Mask account numbers, names │
│  └──────────┬──────────┘                               │
│             │                                           │
│             ▼                                           │
│  ┌─────────────────────┐                               │
│  │  Case Record Creator │ ← Insert into cases table    │
│  └──────────┬──────────┘                               │
│             │                                           │
│             ▼                                           │
│  ┌─────────────────────┐                               │
│  │  Event Queue Push    │ ← Enqueue for Triage Agent   │
│  └─────────────────────┘                               │
│                                                         │
│  Return HTTP 202 ACCEPTED                               │
└─────────────────────────────────────────────────────────┘
```

**Idempotency key:** `alert_id` — if same `alert_id` received twice, return 202 without reprocessing.

---

## 10. FRONTEND — ANALYST DASHBOARD (Component Design)

### 10a. Page Structure

```
App
├── AuthGuard (SSO token validation)
├── Layout
│   ├── Navbar (role-aware: Analyst / Manager / Compliance)
│   └── Sidebar (navigation)
└── Pages
    ├── /dashboard          → KPI summary cards + live alert count
    ├── /cases              → Case queue table (filterable, sortable)
    ├── /cases/:case_id     → Case detail view + AI summary + decision panel
    ├── /query              → Chat-to-Agent (C2A) natural language query
    └── /reports            → Daily report list + download links (Compliance role only)
```

### 10b. Case Detail View — Component Breakdown

```
CaseDetailPage
├── CaseHeader         → case_id, status badge, risk level badge, created_at
├── TransactionCard    → amount, channel, timestamp (masked account)
├── AISummaryCard      → AI rationale, confidence score, recommended action
│                         ⚠️ Warning badge if confidence < 0.7
├── CustomerContextCard→ 90-day history summary (from RAG output)
├── GovernancePanel    → Rules checked: ✅/❌ per rule ID
├── DecisionPanel      → Accept / Modify / Reject buttons
│   ├── AcceptButton   → Confirms AI recommendation
│   ├── ModifyForm     → Override risk level + notes
│   └── RejectForm     → Enter reason for rejection
└── AuditTrailSection  → Chronological log of all actions on this case
```

### 10c. State Management

| State | Location | Notes |
|---|---|---|
| Auth token | HTTP-only cookie | Secure; prevents XSS access |
| Case queue data | Server state (React Query) | Auto-refresh every 60 seconds |
| Selected case detail | Server state (React Query) | Fetched on navigation |
| Analyst decision form | Local component state | Cleared on submit |
| C2A query + response | Local component state | Not persisted |

---

## 11. ENVIRONMENT CONFIGURATION

### 11a. Environment Variables (example — stored in Secrets Vault)

```env
# Application
APP_ENV=poc
APP_PORT=8000
LOG_LEVEL=INFO

# Database
DB_HOST=[FILL]
DB_PORT=5432
DB_NAME=fraud_poc
DB_USER=[FILL]
DB_PASSWORD=[SECRETS_VAULT]

# LLM
LLM_API_ENDPOINT=[FILL]
LLM_API_KEY=[SECRETS_VAULT]
LLM_MODEL_NAME=[FILL]
LLM_MAX_TOKENS=800
LLM_TEMPERATURE=0.1

# Vector Store
VECTOR_STORE_URL=[FILL]
VECTOR_STORE_API_KEY=[SECRETS_VAULT]
EMBEDDING_MODEL=[FILL]
EMBEDDING_DIMENSION=[FILL]

# Message Queue
QUEUE_CONNECTION_STRING=[SECRETS_VAULT]
QUEUE_NAME=fraud-alert-queue

# Blob Storage
BLOB_STORAGE_ACCOUNT=[FILL]
BLOB_CONTAINER_NAME=reports
BLOB_SAS_KEY=[SECRETS_VAULT]

# Auth
AUTH_ISSUER_URL=[FILL]
AUTH_AUDIENCE=[FILL]

# Business Rules
MAX_AUTO_RESOLVE_AMOUNT=50000
MIN_CONFIDENCE_SCORE=0.75
AUTO_RES_RATE_ALERT_THRESHOLD=30.0

# Notifications
OPS_MANAGER_EMAIL=[FILL]
NOTIFICATION_SERVICE_KEY=[SECRETS_VAULT]
```

### 11b. Environments

| Environment | Purpose | Data | Access |
|---|---|---|---|
| `dev` | Local development | Fully synthetic | FSD team only |
| `poc` | POC pilot execution | Anonymised production data | Pilot users + project team |
| `prod` | Future production | Real data | Not in scope for POC |

---

## 12. CI/CD PIPELINE (POC)

```
Developer pushes code to feature branch
        │
        ▼
[Pull Request Created]
        │
        ▼
┌───────────────────────────────────────┐
│  CI Pipeline (auto-triggered)         │
│  1. Lint & code style check           │
│  2. Unit tests (pytest)               │
│  3. Integration tests (mock services) │
│  4. Security scan (SAST)              │
│  5. Docker image build                │
└──────────────────┬────────────────────┘
                   │ All checks pass
                   ▼
[PR Review & Merge to main]
                   │
                   ▼
┌───────────────────────────────────────┐
│  CD Pipeline (manual trigger for POC) │
│  1. Pull latest image                 │
│  2. Deploy to poc environment         │
│  3. Run smoke tests                   │
│  4. Notify team on success/failure    │
└───────────────────────────────────────┘
```

---

## 13. TEST CASE MAPPING

| Test Case ID | Req ID | Description | Type | Expected Result |
|---|---|---|---|---|
| TC-01 | FR-01 | Ingest alert from mock source; verify it appears in system within 5 min | Integration | Alert in DB within 5 min |
| TC-02 | FR-02 | Send 20 pre-labelled test alerts; validate AI classification accuracy | Functional | ≥ 85% match to expert labels |
| TC-03 | FR-04 | Analyst overrides AI classification; verify override is saved | Functional | Override record in DB with analyst ID |
| TC-04 | BR-01 | Send LOW-risk alert with amount above threshold; verify it escalates | Business Rule | Status = ESCALATED; audit log: BR-01 triggered |
| TC-05 | FR-05 | Send 50 LOW-risk alerts within threshold; verify ≥ 40% auto-resolved | Functional | Auto-resolve rate ≥ 40%; no real fraud in auto-resolved set |
| TC-06 | FR-07 | Send LOW-risk alert with amount > max threshold; verify NOT auto-resolved | Business Rule | No auto-resolution; case escalated |
| TC-07 | BR-02 | Send LOW-risk alert for VIP customer; verify escalation | Business Rule | Status = ESCALATED; audit log: BR-02 triggered |
| TC-08 | FR-08 | Medium-risk alert escalated; verify analyst queue updated within 2 min | Functional | Queue updated ≤ 2 min post-triage |
| TC-09 | FR-09 | Escalated case summary contains all 4 required elements | Functional | customer profile ✅ · txn history ✅ · risk indicators ✅ · recommendation ✅ |
| TC-10 | FR-11 | Analyst submits NL query "show high-risk cases today"; verify response | Functional | Accurate case list returned in ≤ 3 sec |
| TC-11 | FR-12 | Run Report Agent for test date; verify report generated by 08:00 AM | Functional | PDF in blob store; report record in DB |
| TC-12 | FR-13 | Process 10 test cases; verify 100% have audit log entries | Compliance | 10/10 audit records found; no gaps |
| TC-13 | NFR-01 | Time alert triage end-to-end for 20 alerts | Performance | All ≤ 30 seconds |
| TC-14 | NFR-04 | Intercept API traffic; verify TLS 1.2+ | Security | No plaintext traffic observed |
| TC-15 | NFR-07 | Inspect audit log entries; verify all required fields present | Compliance | All fields (timestamp, actor, input, decision, confidence) present |
| TC-16 | NFR-09 | UAT with pilot analysts; core tasks in ≤ 3 clicks | Usability | Task completion ≤ 3 clicks validated in UAT session |

---

## 14. NEXT STEPS (after LLD sign-off)

| # | Action | Owner | Sequence |
|---|---|---|---|
| 1 | LLD review & sign-off by Architect + QA Lead | IT Architect, QA | Now |
| 2 | Begin **UX / UI Design** — wireframes & interactive prototype | UX Designer (parallel) | Now |
| 3 | Set up `dev` environment — DB, queue, blob storage | Infra + FSD | Now |
| 4 | Sprint 1: Connector Service + Case DB + Triage Agent | FSD (Aditya Singh) | After sign-off |
| 5 | Sprint 2: Resolution + Escalation Agents + Governance Module | FSD | After Sprint 1 |
| 6 | Sprint 3: Report Agent + Dashboard UI + Query Agent | FSD + UX | After Sprint 2 |
| 7 | Sprint 4: Integration testing + UAT + POC pilot go-live | Full team | After Sprint 3 |

---

*Document Owner: Aditya Singh | Version: 1.0 | Date: October 2026*
*This is a learning exercise document. All technology references are placeholders.*
