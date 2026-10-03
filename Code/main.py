from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import uuid
import csv
import io
import os
from triage_agent import run_local_llm_triage, FraudAlert, run_c2a_query

DATABASE_URL = "sqlite:///./fraud_poc.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CaseDB(Base):
    __tablename__ = "cases"
    case_id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    customer_tier = Column(String)
    status = Column(String, default="PENDING")
    risk_level = Column(String, default="UNKNOWN")
    ai_rationale = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AURA Agentic AI Platform")

class AlertIngestRequest(BaseModel):
    alert_id: str
    amount: float
    channel: str
    customer_tier: str
    ip_location: str
    home_location: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_alert_background(alert_req: AlertIngestRequest, case_id: str):
    db = SessionLocal()
    alert_data = FraudAlert(**alert_req.dict())
    
    # --- NEW RELATIONAL RAG LOGIC ---
    # Query database for recent historical transactions belonging to this customer tier
    past_cases = db.query(CaseDB).filter(
        CaseDB.customer_tier == alert_req.customer_tier,
        CaseDB.case_id != case_id
    ).order_by(CaseDB.created_at.desc()).limit(3).all()
    
    historical_context = "No prior history for this tier."
    if past_cases:
        historical_context = "Recent historical transactions for this customer tier:\n"
        for p in past_cases:
            historical_context += f"- Amount: ${p.amount}, Risk: {p.risk_level}, Status: {p.status}\n"
    
    # Pass the history (RAG) to the AI Agent
    ai_decision = run_local_llm_triage(alert_data, historical_context)
    # --------------------------------
    
    db_case = db.query(CaseDB).filter(CaseDB.case_id == case_id).first()
    if db_case:
        db_case.risk_level = ai_decision.get("risk_level", "ERROR")
        db_case.ai_rationale = ai_decision.get("rationale", "No rationale provided")
        if db_case.risk_level == "LOW":
            db_case.status = "AUTO_RESOLVED"
        else:
            db_case.status = "ESCALATED"
        db.commit()
    db.close()

@app.post("/api/v1/alerts/ingest")
async def ingest_alert(alert: AlertIngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing = db.query(CaseDB).filter(CaseDB.alert_id == alert.alert_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Alert ID already exists")
    new_case_id = str(uuid.uuid4())
    new_case = CaseDB(case_id=new_case_id, alert_id=alert.alert_id, amount=alert.amount, customer_tier=alert.customer_tier)
    db.add(new_case)
    db.commit()
    background_tasks.add_task(process_alert_background, alert, new_case_id)
    return {"status": "ACCEPTED", "case_id": new_case_id}

# --- NEW BULK CSV UPLOAD LOGIC ---
@app.post("/api/v1/alerts/bulk-upload")
async def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    count = 0
    for row in reader:
        try:
            alert = AlertIngestRequest(
                alert_id=row.get('alert_id', str(uuid.uuid4())[:8]),
                amount=float(row.get('amount', 0)),
                channel=row.get('channel', 'Web'),
                customer_tier=row.get('customer_tier', 'Standard'),
                ip_location=row.get('ip_location', 'Unknown'),
                home_location=row.get('home_location', 'Unknown')
            )
            existing = db.query(CaseDB).filter(CaseDB.alert_id == alert.alert_id).first()
            if not existing:
                new_case_id = str(uuid.uuid4())
                new_case = CaseDB(case_id=new_case_id, alert_id=alert.alert_id, amount=alert.amount, customer_tier=alert.customer_tier)
                db.add(new_case)
                background_tasks.add_task(process_alert_background, alert, new_case_id)
                count += 1
        except Exception as e:
            print(f"Skipping CSV row due to error: {e}")
            
    db.commit()
    return {"status": "SUCCESS", "message": f"Successfully ingested {count} alerts in bulk from CSV!"}
# ---------------------------------

@app.get("/api/v1/cases")
def get_cases(db: Session = Depends(get_db)):
    cases = db.query(CaseDB).order_by(CaseDB.created_at.desc()).all()
    return [{"case_id": c.case_id, "alert_id": c.alert_id, "amount": c.amount, "status": c.status, "risk_level": c.risk_level, "ai_rationale": c.ai_rationale, "created_at": c.created_at} for c in cases]

class DecisionReq(BaseModel):
    decision: str

@app.post("/api/v1/cases/{case_id}/decision")
def submit_decision(case_id: str, req: DecisionReq, db: Session = Depends(get_db)):
    db_case = db.query(CaseDB).filter(CaseDB.case_id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404)
    db_case.status = f"CLOSED_{req.decision}"
    db.commit()
    return {"status": "UPDATED"}

class QueryReq(BaseModel):
    query: str

@app.post("/api/v1/cases/{case_id}/query")
def chat_to_agent(case_id: str, req: QueryReq, db: Session = Depends(get_db)):
    db_case = db.query(CaseDB).filter(CaseDB.case_id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404)
    
    case_data = {"alert_id": db_case.alert_id, "amount": db_case.amount, "risk": db_case.risk_level, "rationale": db_case.ai_rationale}
    ans = run_c2a_query(case_data, req.query)
    return {"answer": ans}

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/", StaticFiles(directory="static", html=True), name="static")
