import os
import threading
import time
import uuid
from datetime import datetime
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="NEXO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PING_INTERVAL_SECONDS = 5 * 60
SELF_URL = os.getenv("RENDER_EXTERNAL_URL")


def keep_alive():
    if not SELF_URL:
        return
    while True:
        time.sleep(PING_INTERVAL_SECONDS)
        try:
            requests.get(SELF_URL, timeout=10)
        except requests.RequestException:
            pass


@app.on_event("startup")
def start_keep_alive():
    if SELF_URL:
        threading.Thread(target=keep_alive, daemon=True).start()


departments = {
    "1": {"id": "1", "name": "Contabilidade Fiscal"},
    "2": {"id": "2", "name": "Departamento Pessoal"},
    "3": {"id": "3", "name": "Contabilidade Societária"},
    "4": {"id": "4", "name": "Administrativo"},
    "5": {"id": "5", "name": "Folha de Pagamento"},
    "6": {"id": "6", "name": "Fiscal"},
    "7": {"id": "7", "name": "Contábil"},
    "8": {"id": "8", "name": "Recepção"},
    "9": {"id": "9", "name": "Auxiliar Contábil"},
}

feedbacks = []


class FeedbackIn(BaseModel):
    type: Literal["up", "down"]
    message: str = Field(min_length=1, max_length=400)


def department_with_counts(department_id: str) -> dict:
    department = departments[department_id]
    department_feedbacks = [f for f in feedbacks if f["department_id"] == department_id]
    return {
        **department,
        "up": sum(1 for f in department_feedbacks if f["type"] == "up"),
        "down": sum(1 for f in department_feedbacks if f["type"] == "down"),
    }


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/departments")
def get_departments():
    return [department_with_counts(did) for did in departments]


@app.get("/departments/{department_id}")
def get_department(department_id: str):
    if department_id not in departments:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return department_with_counts(department_id)


@app.get("/departments/{department_id}/feedbacks")
def get_feedbacks(department_id: str):
    if department_id not in departments:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    department_feedbacks = [f for f in feedbacks if f["department_id"] == department_id]
    return sorted(department_feedbacks, key=lambda f: f["timestamp"], reverse=True)


@app.post("/departments/{department_id}/feedbacks", status_code=201)
def create_feedback(department_id: str, payload: FeedbackIn):
    if department_id not in departments:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")

    feedback = {
        "id": str(uuid.uuid4()),
        "department_id": department_id,
        "type": payload.type,
        "message": payload.message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    feedbacks.append(feedback)
    return feedback
