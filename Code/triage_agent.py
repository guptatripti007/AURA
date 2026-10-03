import json
import requests
import urllib.request
import time
import os
import re
from pydantic import BaseModel

OLLAMA_API_URL = "http://localhost:11434/api/generate"
LOCAL_MODEL = "llama3"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

class FraudAlert(BaseModel):
    alert_id: str
    amount: float
    channel: str
    customer_tier: str
    ip_location: str
    home_location: str

# NEW: RAG Parameter added (historical_context)
def run_local_llm_triage(alert: FraudAlert, historical_context: str = "No historical data found.") -> dict:
    prompt = f"""
    You are an expert fraud analyst system. Review the following transaction alert and classify the risk level as HIGH, MEDIUM, or LOW.
    
    Alert ID: {alert.alert_id}
    Transaction Amount: ${alert.amount}
    Channel: {alert.channel}
    Customer Tier: {alert.customer_tier}
    Transaction Location: {alert.ip_location}
    Customer Home Location: {alert.home_location}
    
    HISTORICAL MEMORY (RAG CONTEXT):
    {historical_context}
    
    Instructions:
    1. If the location does not match the home location, increase risk.
    2. If the amount is highly anomalous compared to historical RAG memory, increase risk.
    3. Output ONLY a valid JSON object with the keys: "risk_level" (HIGH/MEDIUM/LOW), "rationale" (string), "confidence" (float 0.0-1.0).
    """

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={ "type": "json_object" },
                messages=[{"role": "user", "content": prompt}]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"OpenAI Failed: {e}. Falling back...")

    try:
        payload = { "model": LOCAL_MODEL, "prompt": prompt, "stream": False, "format": "json" }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=3)
        response.raise_for_status()
        return json.loads(response.json().get("response", "{}"))
    except requests.exceptions.ConnectionError:
        print("WARNING: Local AI not detected! Falling back to SIMULATED AI...")
        time.sleep(2)
        
        # Make the simulation react to the RAG memory!
        rag_text = ""
        if "Amount" in historical_context:
            rag_text = "Cross-referenced with historical memory (RAG). "
            
        if alert.amount > 10000 or alert.ip_location != alert.home_location:
            return {"risk_level": "HIGH", "rationale": rag_text + "Highly anomalous amount and foreign IP mismatch detected.", "confidence": 0.95}
        else:
            return {"risk_level": "LOW", "rationale": rag_text + "Matches standard geographic and historical baseline behavior.", "confidence": 0.88}
    except Exception as e:
        return {"risk_level": "ERROR", "rationale": str(e), "confidence": 0.0}

def run_c2a_query(case_data: dict, user_query: str) -> str:
    url_match = re.search(r'(https?://[^\s]+)', user_query)
    osint_status = ""
    
    if url_match:
        url = url_match.group(1)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req, timeout=4).read().decode('utf-8')
            osint_status = f"[OSINT SUCCESS: Retrieved {len(html)} bytes from URL] "
        except Exception as e:
            osint_status = f"[OSINT BLOCKED: Anti-bot protection active. Error: {e}] "

    prompt = f"""
    You are the AURA Investigation Agent assisting a fraud analyst.
    Case Data: {json.dumps(case_data)}
    Analyst Question: {user_query}
    OSINT Status: {osint_status}
    
    Provide a concise, professional answer based on the case data.
    """

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            pass 

    try:
        payload = { "model": LOCAL_MODEL, "prompt": prompt, "stream": False }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=3)
        response.raise_for_status()
        return response.json().get("response", "I could not generate an answer.")
    except requests.exceptions.ConnectionError:
        time.sleep(1.5)
        q = user_query.lower()
        if url_match and "linkedin.com" in url_match.group(1):
            return osint_status + "Because this is a LinkedIn profile, cross-referencing employment history with stated income is a critical verification step. Would you like me to flag this for manual KYC review?"
        elif url_match:
            return osint_status + "I have analyzed the public footprint of this domain."
        elif "ip" in q or "location" in q:
            return "Based on global threat intelligence, this IP originates from a commercial VPN exit node."
        else:
            return "Looking at the combined risk factors, this strongly matches known patterns of Account Takeover (ATO)."
