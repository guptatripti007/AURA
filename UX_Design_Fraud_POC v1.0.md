# UX / UI Design Specification
### Fraud Detection & Resolution Automation — BFSI POC

---

| Field | Details |
|---|---|
| **Document Version** | v1.0 |
| **Prepared By** | Aditya Singh |
| **Organisation** | Self Learning |
| **Date** | October 2026 |
| **Status** | Draft |
| **Refers To** | HLR/BRD v1.0 ✅ · HLD v1.0 ✅ · LLD v1.0 ✅ |

---

## 1. DESIGN PRINCIPLES

1. **Information Density with Clarity:** Analysts need a lot of data quickly. Use cards, clear typography, and color-coded risk tags to guide the eye without overwhelming them.
2. **AI Transparency:** Clearly separate raw transaction data from AI-generated insights. Always show a "Confidence Score".
3. **One-Click Actions:** Core actions (Accept AI Recommendation, Escalate) should require minimal clicks.
4. **Auditability Visibility:** Remind users that actions are logged (e.g., "Decision will be recorded in the audit log").

---

## 2. USER JOURNEYS

### Journey 1: Fraud Analyst Triage
1. Logs into the platform via SSO.
2. Lands on the **Analyst Dashboard (Queue)**. Sees cases assigned to them, sorted by Risk Level (High first).
3. Clicks on the top case to open the **Case Detail View**.
4. Reviews the `Transaction Details` and the `AI Case Summary`.
5. Checks the `Governance Panel` to see which rules passed/failed.
6. Clicks **[ Accept AI Recommendation ]** (e.g., Close as False Positive).
7. System briefly shows a success toast ("Decision Logged") and auto-loads the next case.

### Journey 2: Chat-to-Agent (C2A) Investigation
1. Analyst is unsure about a complex case.
2. Opens the **Query Agent Sidebar**.
3. Types: *"Has this customer had similar velocity alerts in the last 6 months?"*
4. AI queries the RAG backend and responds with a summarized timeline and links to previous closed cases.

---

## 3. TEXT-BASED WIREFRAMES

### Screen 1: Analyst Dashboard (Queue)

```text
[ Logo: Self Learning ]    [ Search Cases... 🔍 ]    [👤 Analyst Name ] [🔔 3]
─────────────────────────────────────────────────────────────────────────────
 📊 OVERVIEW (Today)
 [ Escalated: 12 ]   [ Auto-Resolved: 45 ]   [ Avg Triage Time: 4m ]

 📋 MY CASE QUEUE 
 [ Filters: ▽ Risk Level ] [ ▽ Status ] [ ▽ Date ]            [ Refresh ↻ ]

 RISK   | CASE ID   | TXN AMOUNT | AI REC.          | CONFIDENCE | ACTION
 ────────────────────────────────────────────────────────────────────────
 🔴 HIGH | CS-8991   | $ 12,450   | BLOCK & REVIEW   | 92%        | [Review]
 🔴 HIGH | CS-8990   | $ 8,200    | BLOCK & REVIEW   | 88%        | [Review]
 🟠 MED  | CS-8985   | $ 1,150    | CALL CUSTOMER    | 75%        | [Review]
 🟠 MED  | CS-8982   | $ 800      | MONITOR          | 81%        | [Review]

                                                      [ < Prev ] [ 1 ] [ Next > ]
```

### Screen 2: Case Detail View (The Core Workspace)

```text
[ ← Back to Queue ]                            [ Case ID: CS-8991 ]  [ 🔴 HIGH RISK ]
─────────────────────────────────────────────────────────────────────────────
 💳 TRANSACTION DETAILS                     |  🤖 AI CASE SUMMARY
 Txn ID:    TXN-9001123                     |  Recommendation: BLOCK ACCOUNT
 Amount:    $ 12,450.00                     |  Confidence: [████████░░] 92%
 Channel:   Online Banking (Web)            |  
 Time:      2026-10-02 14:30 UTC            |  Rationale: 
 Account:   **** 4432 (Standard Tier)       |  Transaction amount is 5x higher 
 Location:  IP: 192.168.x.x (Unknown Dev)   |  than user's 90-day average. Device 
                                            |  IP does not match home location.
────────────────────────────────────────────|  Matches pattern of Account Takeover.
 📜 CUSTOMER CONTEXT (From RAG)             |
 - Customer Tenure: 4 Years                 |  ──────────────────────────────────
 - 90-Day Avg Txn: $ 2,100                  |  🛡️ GOVERNANCE CHECK
 - Previous Fraud Flags: 0                  |  [✅] BR-01: Amount limit check
 - KYC Status: Verified                     |  [✅] GR-02: Rationale generated
                                            |  [✅] GR-03: No PII in output
─────────────────────────────────────────────────────────────────────────────
 ⚡ DECISION PANEL
 What action would you like to take?

 [ ✅ ACCEPT AI RECOMMENDATION ]   [ ✏️ MODIFY ACTION ]   [ ❌ REJECT (ESCALATE) ]
 (Block Account)                   (Change parameters)    (Send to L2 Team)
```

### Screen 3: Query Agent (Slide-out Sidebar)

```text
 ┌──────────────────────────────────────────┐
 │ 💬 QUERY AGENT (C2A)                  [X]│
 │──────────────────────────────────────────│
 │                                          │
 │ [System]: I am ready to assist with      │
 │ case CS-8991.                            │
 │                                          │
 │ [Analyst]: What is the exact IP location │
 │ of this transaction?                     │
 │                                          │
 │ [Agent]: The IP resolves to a VPN exit   │
 │ node in Eastern Europe. The customer's   │
 │ registered address is in Mumbai, India.  │
 │ (Source: Geo-IP DB / Profile)            │
 │                                          │
 │ ──────────────────────────────────────── │
 │ [ Ask a question about this case...    ] │
 │                                    [ > ] │
 └──────────────────────────────────────────┘
```

---

## 4. DESIGN SYSTEM SPECIFICATIONS

### 4a. Typography & Colors
*   **Font:** Inter or Roboto (Clean, highly legible for data-heavy screens).
*   **Primary Brand:** Deep Navy Blue `#0A192F`
*   **Risk Colors (Crucial for at-a-glance triage):**
    *   `HIGH RISK`: Red `#E63946`
    *   `MEDIUM RISK`: Orange `#F4A261`
    *   `LOW RISK`: Green `#2A9D8F` (Mostly seen in manager dashboards, as these are auto-resolved).
*   **Confidence Scores:**
    *   > 85%: Green text
    *   70% - 85%: Yellow/Orange text
    *   < 70%: Red text with a warning icon (⚠️)

### 4b. Component Library (To be built in React)
1.  **Data Table:** Sortable, paginated, sticky headers.
2.  **Status Badges:** Pill-shaped tags for Risk and Status.
3.  **Progress/Confidence Bar:** Visual indicator for AI certainty.
4.  **Toast Notifications:** Non-intrusive alerts for successful actions ("Case Saved").
5.  **Slide-out Drawer:** Used for the Chat-to-Agent interface to avoid navigating away from the case context.

---

## 5. ACCESSIBILITY & RESPONSIVENESS
*   **Viewport:** Desktop-first (1080p target). Fraud analysts do not triage cases on mobile devices.
*   **Accessibility:** ARIA labels on all AI recommendation buttons. Color contrast ratio must meet WCAG AA standards (especially for Risk text).

---
*Next Phase: Technical implementation / POC Build sprints.*
