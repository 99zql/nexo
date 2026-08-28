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


employees = {
    "1": {"id": "1", "name": "Samuel", "role": "Assistente Contábil"},
    "2": {"id": "2", "name": "Sophia", "role": "Analista Fiscal"},
    "3": {"id": "3", "name": "Lucas", "role": "Contador Responsável"},
    "4": {"id": "4", "name": "Murillo", "role": "Auxiliar Administrativo"},
    "5": {"id": "5", "name": "Luis", "role": "Analista de Folha de Pagamento"},
    "6": {"id": "6", "name": "Giovanna", "role": "Assistente Fiscal"},
    "7": {"id": "7", "name": "Felipe", "role": "Analista Contábil"},
    "8": {"id": "8", "name": "Maria Luiza", "role": "Recepcionista"},
    "9": {"id": "9", "name": "Gabriel", "role": "Auxiliar Contábil"},
}

feedbacks = []


class FeedbackIn(BaseModel):
    type: Literal["up", "down"]
    message: str = Field(min_length=1, max_length=400)


def employee_with_counts(employee_id: str) -> dict:
    employee = employees[employee_id]
    employee_feedbacks = [f for f in feedbacks if f["employee_id"] == employee_id]
    return {
        **employee,
        "up": sum(1 for f in employee_feedbacks if f["type"] == "up"),
        "down": sum(1 for f in employee_feedbacks if f["type"] == "down"),
    }


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/employees")
def get_employees():
    return [employee_with_counts(eid) for eid in employees]


@app.get("/employees/{employee_id}")
def get_employee(employee_id: str):
    if employee_id not in employees:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    return employee_with_counts(employee_id)


@app.get("/employees/{employee_id}/feedbacks")
def get_feedbacks(employee_id: str):
    if employee_id not in employees:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    employee_feedbacks = [f for f in feedbacks if f["employee_id"] == employee_id]
    return sorted(employee_feedbacks, key=lambda f: f["timestamp"], reverse=True)


@app.post("/employees/{employee_id}/feedbacks", status_code=201)
def create_feedback(employee_id: str, payload: FeedbackIn):
    if employee_id not in employees:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    feedback = {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "type": payload.type,
        "message": payload.message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    feedbacks.append(feedback)
    return feedback
