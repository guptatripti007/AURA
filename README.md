# AURA (Autonomous Resolution Agent)

AURA is an enterprise-grade Agentic AI platform designed to automate the triage and resolution of Level 1 fraud alerts in the Banking, Financial Services, and Insurance (BFSI) sector.

## 🚀 The Problem
Modern fraud operations teams are overwhelmed by "noise." Analysts spend up to 15 minutes manually reviewing transactions, the majority of which are false positives. This creates massive backlogs, delays genuine threat response, and drives up operational costs.

## 💡 The Solution
AURA acts as a highly intelligent, autonomous frontline sentinel. It ingests transaction data and utilizes a local/cloud LLM to make instant, context-aware risk decisions.
* **Low Risk:** Autonomously resolved and closed (False Positives).
* **High Risk:** Escalated to a human analyst with a plain-English rationale.

## ⚙️ Key Features
* **AI Auto-Resolution:** Reduces manual L1 triage volume by >40%.
* **Human-in-the-Loop UI:** A modern dashboard for human analysts to review AI decisions, complete with Accept/Override controls.
* **C2A (Chat-to-Agent) OSINT:** Analysts can chat directly with the AI inside the case panel. Paste a URL, and AURA will utilize Open Source Intelligence (OSINT) to scan the web and enrich the investigation.
* **Regulatory Compliance Reports:** Automatically generates immutable, daily PDF audit logs proving 100% adherence to governance rules.

## 🛠️ Tech Stack
* **Backend:** Python, FastAPI, SQLite, SQLAlchemy
* **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla), jsPDF
* **AI/LLM Integration:** OpenAI (GPT-4o-mini) / Local Ollama Fallback

## 🏃‍♂️ How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Add your OpenAI API key to the `.env` file (optional, will use simulated AI if left blank).
4. Start the server: `uvicorn Code.main:app --reload`
5. Open your browser to `http://localhost:8000/`

---
*Developed by Aditya Singh for Self Learning & Enterprise POC Demonstration.*
