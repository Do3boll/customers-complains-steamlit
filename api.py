"""
Run
 pip install fastapi uvicorn pydantic requests
    uvicorn api:app --reload --port 8000

Then
      POST http://localhost:8000/process-customer-message
"""

import logging
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from prompts import build_prompt, ROUTING_OPTIONS
from llm import generate_json

# Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("customer_intelligence.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("customer_intelligence.api")

app = FastAPI(
    title="LLM-Based Customer Intelligence System",
    description="Processes a customer message into structured intent, priority, "
                "routing, explanation and suggested action.",
    version="1.0.0",
)

class CustomerMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Raw customer message text")


class CustomerMessageResponse(BaseModel):
    request_id: str
    intent: List[str]
    issue_type: str
    priority: str
    entities: List[str]
    routing: str
    suggested_action: str
    explanation: str
    response: str
    latency_ms: int


# Validation / normalization of whatever the LLM returns
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}


def _normalize_llm_output(raw: dict) -> dict:
    intent = raw.get("intent", [])
    if isinstance(intent, str):
        intent = [intent]

    entities = raw.get("entities", [])
    if isinstance(entities, str):
        entities = [entities] if entities else []

    priority = raw.get("priority", "Medium")
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    routing = raw.get("routing", "Support Team")
    if routing not in ROUTING_OPTIONS:
        routing = "Support Team"

    return {
        "intent": intent or ["Unclear"],
        "issue_type": raw.get("issue_type", "Unspecified"),
        "priority": priority,
        "entities": entities,
        "routing": routing,
        "suggested_action": raw.get("suggested_action", "Route to a human agent for review"),
        "explanation": raw.get("explanation", "No explanation provided by model."),
        "response": raw.get("response", "Thank you for reaching out, our team is reviewing your request."),
    }


# Endpoint
@app.post("/process-customer-message", response_model=CustomerMessageResponse)
def process_customer_message(payload: CustomerMessageRequest):
    request_id = str(uuid.uuid4())
    start = time.time()

    logger.info("request_id=%s | incoming message: %s", request_id, payload.message)

    prompt = build_prompt(payload.message)

    try:
        raw_output = generate_json(prompt)
    except Exception as e:
        logger.error("request_id=%s | LLM processing failed: %s", request_id, e)
        raise HTTPException(status_code=502, detail=f"LLM processing failed: {e}")

    normalized = _normalize_llm_output(raw_output)
    latency_ms = int((time.time() - start) * 1000)

    logger.info(
        "request_id=%s | output=%s | latency_ms=%d",
        request_id, normalized, latency_ms,
    )

    return CustomerMessageResponse(
        request_id=request_id,
        latency_ms=latency_ms,
        **normalized,
    )


@app.get("/health")
def health():
    return {"status": "ok"}

'''
{


{
  "message": "Someone tried to log into my account from a different country. I did not authorize this."
}

{
  "message": "I was charged twice for the same transaction and I need this resolved immediately. If not, I will escalate."
}


  "request_id": "b1e2...",
  "intent": ["Billing Issue", "Complaint"],
  "issue_type": "Duplicate charge on transaction",
  "priority": "High",
  "entities": ["duplicate transaction"],
  "routing": "Billing Department",
  "suggested_action": "Escalate and verify transaction logs",
  "explanation": "The customer reports a duplicate charge and threatens escalation, indicating a billing error with urgency.",
  "response": "We're sorry for the inconvenience - we're verifying the duplicate charge now and will resolve it within 24 hours.",
  "latency_ms": 842
'''