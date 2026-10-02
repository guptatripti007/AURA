# High-Level Requirements (HLR) / Business Requirements Document (BRD)
### Fraud Detection & Resolution Automation — BFSI POC

---

| Field | Details |
|---|---|
| **Document Version** | v1.0 |
| **Prepared By** | Aditya Singh |
| **Organisation** | Self Learning |
| **Date** | October 2026 |
| **Status** | Draft |
| **Refers To** | Business Case v1.0 (✅ Approved) |
| **Classification** | Internal / Confidential |

---

## 1. PURPOSE & SCOPE

### 1a. Purpose

This document defines the **high-level business requirements** for the Fraud Detection & Resolution Automation POC. It captures *what* the system must do — not *how* it will be built (that is addressed in the Low-Level Design). It serves as the agreement between business stakeholders and the technical team before design and development begin.

### 1b. In Scope (POC)

- Automated ingestion of real-time fraud alerts from **1 source system** (to be confirmed)
- AI-driven triage and classification of fraud alerts (High / Medium / Low risk)
- Autonomous resolution of **low-risk false positive** alerts without analyst intervention
- Escalation of **medium and high-risk** cases to human analysts with pre-built case summaries
- Auto-generation of compliance-ready case reports
- Audit trail for every AI decision made during the POC
- Pilot with a defined group of fraud analysts (`[FILL: X users]`)

### 1c. Out of Scope (POC)

- Integration with more than 1 source system
- Real-time transaction blocking / card freeze (production action)
- Full production deployment
- Mobile application or customer-facing interface
- Training or retraining of underlying AI/ML models
- Multi-geography or multi-language support
- Third-party credit bureau data integration

---

## 2. BACKGROUND & CONTEXT

The organisation's fraud operations team currently handles all alert triage and case resolution manually. Key pain points identified in the approved Business Case:

- Average fraud case resolution: `[FILL]` days
- High false-positive rate causing analyst fatigue
- No single unified view of customer fraud history across systems
- Manual, time-consuming compliance reporting
- Inability to scale during peak fraud periods

The POC will validate whether an **Agentic AI platform** can autonomously handle a meaningful portion of this workflow, reducing resolution time and freeing analysts for higher-value judgement tasks.

---

## 3. STAKEHOLDERS

| Stakeholder | Role | Interest in This Document |
|---|---|---|
| **Executive Sponsor** | `[FILL]` | Ensures business objectives are captured |
| **Fraud Operations Lead** | `[FILL]` | Primary subject matter expert; validates business rules |
| **Business Analyst** | `[FILL]` | Authors and maintains this document |
| **Full Stack Developer (FSD)** | Aditya Singh | Consumes requirements to design and build the solution |
| **IT / Cloud Architect** | `[FILL]` | Reviews integration and non-functional requirements |
| **Legal / Compliance Officer** | `[FILL]` | Reviews data, audit, and regulatory requirements |
| **QA / Testing Lead** | `[FILL]` | Derives test cases from acceptance criteria |

---

## 4. USER PERSONAS

### Persona 1 — Fraud Analyst (Primary User)
- **Who:** Mid-level bank employee handling 30–80 fraud alerts/day
- **Goal:** Resolve cases faster; focus on complex, high-value fraud
- **Pain today:** Manually reviews every alert; spends 60–70% of time on false positives
- **Expectation from system:** Auto-close obvious false positives; give me a ready case file for real fraud

### Persona 2 — Fraud Operations Manager (Secondary User)
- **Who:** Team lead overseeing 10–20 analysts
- **Goal:** Improve team throughput; meet SLA targets; produce regulatory reports
- **Pain today:** No real-time dashboard; manual weekly reporting
- **Expectation from system:** Live dashboard of all cases; auto-generated compliance reports

### Persona 3 — Compliance Officer (Reviewer)
- **Who:** Internal audit/compliance team member
- **Goal:** Ensure every AI decision is documented and explainable for regulators
- **Pain today:** Relies on analysts to manually document decisions
- **Expectation from system:** Full audit trail for every automated action; exportable logs

---

## 5. FUNCTIONAL REQUIREMENTS

> **Priority Legend:** P1 = Must Have (POC blocker) | P2 = Should Have | P3 = Nice to Have

### 5a. Alert Ingestion & Triage

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-01 | The system shall ingest fraud alerts from the designated source system in real-time or near-real-time (≤ 5 min delay) | P1 | Alerts appear in system within 5 minutes of generation in source |
| FR-02 | The system shall classify each ingested alert as **High / Medium / Low** risk using AI-based reasoning | P1 | Classification accuracy ≥ 85% vs. expert analyst benchmark (UAT) |
| FR-03 | The system shall display the reason for each classification in plain language | P1 | Reason text visible against every classified alert |
| FR-04 | The system shall support a manual override of AI classification by an authorised analyst | P2 | Override action logged with analyst ID, timestamp, and reason |

### 5b. Autonomous Resolution

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-05 | The system shall **automatically resolve and close** Low-risk alerts classified as false positives, without analyst intervention | P1 | ≥ 40% of total alerts auto-resolved; zero real fraud cases auto-closed (validated via QA audit) |
| FR-06 | For auto-resolved cases, the system shall generate and store a resolution record with full AI decision rationale | P1 | 100% of auto-closed cases have a stored resolution record |
| FR-07 | The system shall never auto-resolve any alert where the transaction value exceeds `[FILL: ₹/$X threshold]` | P1 | No auto-resolved case found above threshold in audit log |

### 5c. Analyst Escalation & Case Summary

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-08 | The system shall escalate Medium and High-risk alerts to the fraud analyst queue within 2 minutes of classification | P1 | Escalation timestamp recorded; ≤ 2 min lag confirmed in logs |
| FR-09 | Each escalated case shall include an AI-generated **case summary** containing: customer profile, transaction history, risk indicators, and recommended action | P1 | All 4 elements present in 100% of escalated case summaries |
| FR-10 | Analysts shall be able to accept, modify, or reject the AI-recommended action | P1 | Accept / Modify / Reject action recorded against every escalated case |
| FR-11 | The system shall support natural language querying of case status (e.g., "Show me all high-risk cases from today") | P2 | Query returns accurate results in ≤ 3 seconds |

### 5d. Compliance Reporting

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-12 | The system shall auto-generate a daily fraud operations summary report | P1 | Report generated by 08:00 AM each day; includes total alerts, auto-resolved %, escalated %, resolution time avg |
| FR-13 | The system shall maintain a tamper-proof audit log of every AI action taken during the POC | P1 | Audit log entries immutable; accessible to Compliance Officer |
| FR-14 | Audit logs shall be exportable in PDF and CSV format | P2 | Export function available; exported file is human-readable |

### 5e. Dashboard & Monitoring

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-15 | The system shall provide a real-time dashboard showing: live alert queue, resolution status, KPI metrics | P2 | Dashboard refreshes every 60 seconds; all 3 data elements present |
| FR-16 | The Fraud Operations Manager shall receive an automated alert if the auto-resolution rate drops below 30% | P3 | Alert sent within 5 minutes of threshold breach |

---

## 6. NON-FUNCTIONAL REQUIREMENTS (NFR)

| Req ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-01 | **Performance** | Alert triage (classify + route) completed end-to-end | ≤ 30 seconds per alert |
| NFR-02 | **Availability** | System uptime during POC pilot weeks | ≥ 99% |
| NFR-03 | **Scalability** | System must handle peak load of `[FILL: X]` simultaneous alerts | No degradation in triage time |
| NFR-04 | **Security** | All data in transit encrypted | TLS 1.2+ enforced |
| NFR-05 | **Security** | All data at rest encrypted | AES-256 or equivalent |
| NFR-06 | **Data Privacy** | No real customer PII used during POC | Anonymised/synthetic data only; confirmed by Legal |
| NFR-07 | **Auditability** | Every AI decision logged with timestamp, input data, decision, and confidence score | 100% coverage |
| NFR-08 | **Explainability** | AI decisions must be explainable in plain English | Human-readable rationale present on all decisions |
| NFR-09 | **Usability** | Fraud analyst can complete core tasks (review, override, escalate) within 3 clicks | Validated in UAT |
| NFR-10 | **Compliance** | System architecture must not violate `[FILL: RBI / GDPR / applicable regulation]` data residency rules | Legal sign-off obtained before go-live |
| NFR-11 | **Integration** | Source system connector must not impact performance of source system | Source system team sign-off |

---

## 7. BUSINESS RULES

| BR ID | Business Rule |
|---|---|
| BR-01 | No transaction above `[FILL: ₹/$X]` may be auto-resolved without human analyst review |
| BR-02 | Any fraud case involving a `[FILL: VIP / priority customer tier]` must always be escalated to a senior analyst, regardless of AI risk classification |
| BR-03 | Auto-resolved cases must be retained in the system for a minimum of `[FILL: 7 years]` per regulatory requirement |
| BR-04 | AI recommendations are advisory only — final resolution authority remains with the human analyst for all escalated cases |
| BR-05 | All system access must be role-based; analysts may not access cases outside their assigned queue |
| BR-06 | Compliance reports must be generated and stored in the system before 08:00 AM each business day |

---

## 8. DATA REQUIREMENTS

| Data Element | Source | Used For | Sensitivity |
|---|---|---|---|
| Fraud alert payload | `[FILL: source system]` | Alert ingestion | High |
| Customer transaction history (last 90 days) | `[FILL: core banking / data warehouse]` | Case summary generation | High |
| Customer profile data (anonymised) | `[FILL: CRM]` | Risk classification context | Medium |
| Past fraud case outcomes | `[FILL: fraud case management system]` | AI model context (RAG) | High |
| Fraud policy rules (internal documents) | Policy repository | AI governance rules | Medium |
| Analyst decisions & overrides | System-generated | Audit trail, feedback loop | Medium |

> [!IMPORTANT]
> All data used during the POC must be **anonymised or synthetic**. Legal/Compliance sign-off is a prerequisite before POC environment setup. Real customer PII must not enter the POC environment.

---

## 9. INTEGRATION LANDSCAPE (HIGH LEVEL)

```
[Source System: FILL]
        │  (Fraud Alerts — real-time feed)
        ▼
[Agentic AI Platform — POC Environment]
        │
        ├──► [Knowledge Base: Internal fraud policies + past case data (RAG)]
        │
        ├──► [Analyst Dashboard / Case Queue — Web UI]
        │
        ├──► [Compliance Report Store — PDF/CSV export]
        │
        └──► [Audit Log Repository — immutable, exportable]
```

**Integration approach for POC:** Single API connector to `[FILL: source system]`. All other data via file-based upload (synthetic/anonymised) to the platform's knowledge layer.

---

## 10. ASSUMPTIONS

- Business requirements in this document are based on the approved Business Case
- The Fraud Operations Lead will be available for at least 4 hours/week during the POC for SME review
- Anonymised data will be prepared and signed off by Legal before Week 2 of POC
- Only 1 source system will be integrated during the POC
- The UI will be web-based; no mobile interface is required for the POC
- The AI platform will be deployed on cloud infrastructure agreed by IT

---

## 11. CONSTRAINTS

- POC duration: maximum **8 weeks**
- Budget: `[FILL: ₹/$ X]` (from approved Business Case)
- Integration limited to **1 source system**
- No production data; anonymised/synthetic only
- Regulatory approval for cloud deployment must be obtained before Week 1

---

## 12. REQUIREMENTS TRACEABILITY MATRIX (RTM)

| Req ID | Business Objective (from Business Case) | Priority | Owner | Test Case ID |
|---|---|---|---|---|
| FR-01 | Reduce fraud resolution time | P1 | FSD | TC-01 |
| FR-02 | Reduce fraud resolution time | P1 | FSD | TC-02 |
| FR-05 | Reduce analyst manual effort | P1 | FSD | TC-05 |
| FR-08 | Reduce fraud resolution time | P1 | FSD | TC-08 |
| FR-09 | Reduce analyst manual effort | P1 | BA + FSD | TC-09 |
| FR-12 | Compliance reporting automation | P1 | FSD | TC-12 |
| FR-13 | Governance & auditability (KPI 4) | P1 | FSD | TC-13 |
| NFR-07 | Governance & auditability (KPI 4) | P1 | Architect | TC-20 |
| NFR-09 | Analyst satisfaction (KPI 6) | P1 | UX + FSD | TC-25 |

---

## 13. NEXT STEPS (after HLR/BRD sign-off)

| # | Action | Owner | Sequence |
|---|---|---|---|
| 1 | Stakeholder review & sign-off of this BRD | All stakeholders | Now |
| 2 | Begin **High-Level Design (HLD) / Reference Architecture** | IT Architect + FSD | Next |
| 3 | Begin **UX / UI Design** (parallel to HLD) | UX Designer | Parallel |
| 4 | Finalise anonymised dataset with Legal | Legal + Data team | Now |
| 5 | Confirm source system API access with IT | IT team | Now |

---

*Document Owner: Aditya Singh | Version: 1.0 | Date: October 2026*
*This is a learning exercise document. All vendor references are intentionally generic.*
