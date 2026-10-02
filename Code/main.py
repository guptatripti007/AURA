from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import uuid
import os

from triage_agent import run_local_llm_triage, FraudAlert, run_c2a_query

SQLALCHEMY_DATABASE_URL = "sqlite:///./fraud_poc.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CaseDB(Base):
    __tablename__ = "cases"
    case_id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    customer_tier = Column(String)
    risk_level = Column(String, nullable=True)
    ai_rationale = Column(String, nullable=True)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fraud Automation POC - Local API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class AlertIngestRequest(BaseModel):
    alert_id: str; amount: float; channel: str; customer_tier: str; ip_location: str; home_location: str

class CaseResponse(BaseModel):
    case_id: str; alert_id: str; amount: float; risk_level: str | None; status: str; ai_rationale: str | None
    class Config: from_attributes = True

class CaseDecisionRequest(BaseModel):
    decision: str
    notes: str | None = None

# NEW: Schema for Chat Query
class C2AQueryRequest(BaseModel):
    query: str

def process_alert_background(alert_req: AlertIngestRequest, case_id: str):
    db = SessionLocal()
    try:
        alert_data = FraudAlert(**alert_req.dict())
        ai_decision = run_local_llm_triage(alert_data)
        
        db_case = db.query(CaseDB).filter(CaseDB.case_id == case_id).first()
        if db_case:
            risk = ai_decision.get("risk_level", "ERROR")
            db_case.risk_level = risk
            db_case.ai_rationale = ai_decision.get("rationale", "No rationale provided")
            db_case.status = "AUTO_RESOLVED" if risk == "LOW" else "ESCALATED"
            db.commit()
    finally: db.close()

@app.post("/api/v1/alerts/ingest", status_code=202)
def ingest_alert(alert: AlertIngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing = db.query(CaseDB).filter(CaseDB.alert_id == alert.alert_id).first()
    if existing: return {"status": "ACCEPTED", "message": "Duplicate ignored."}

    new_case_id = str(uuid.uuid4())
    new_case = CaseDB(case_id=new_case_id, alert_id=alert.alert_id, amount=alert.amount, customer_tier=alert.customer_tier)
    db.add(new_case)
    db.commit()

    background_tasks.add_task(process_alert_background, alert, new_case_id)
    return {"status": "ACCEPTED", "internal_case_id": new_case_id}

@app.get("/api/v1/cases", response_model=list[CaseResponse])
def get_cases(db: Session = Depends(get_db)):
    return db.query(CaseDB).order_by(CaseDB.created_at.desc()).all()

@app.post("/api/v1/cases/{case_id}/decision")
def submit_decision(case_id: str, req: CaseDecisionRequest, db: Session = Depends(get_db)):
    db_case = db.query(CaseDB).filter(CaseDB.case_id == case_id).first()
    if not db_case: raise HTTPException(404, "Case not found")
    db_case.status = "CLOSED (Accepted AI)" if req.decision == "ACCEPT" else "CLOSED (Overridden)"
    db.commit()
    return {"status": "SUCCESS", "case_id": case_id, "new_status": db_case.status}

# NEW: Endpoint for Chat-to-Agent
@app.post("/api/v1/cases/{case_id}/query")
def case_query(case_id: str, req: C2AQueryRequest, db: Session = Depends(get_db)):
    db_case = db.query(CaseDB).filter(CaseDB.case_id == case_id).first()
    if not db_case: raise HTTPException(404, "Case not found")
    
    case_data = {
        "alert_id": db_case.alert_id,
        "amount": db_case.amount,
        "customer_tier": db_case.customer_tier,
        "risk_level": db_case.risk_level
    }
    
    answer = run_c2a_query(case_data, req.query)
    return {"answer": answer}

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui(): return FileResponse("static/index.html")
