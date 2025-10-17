from fastapi import APIRouter, HTTPException, BackgroundTasks
from core.models import TaskRequest
from core.config import STUDENT_SECRET
from core.worker import queue

router = APIRouter()

@router.post("/api/task")
async def receive_task(req: TaskRequest, background_tasks: BackgroundTasks):
    if req.secret != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="invalid secret")
    background_tasks.add_task(queue.put, req.dict())
    return {"status": "accepted", "task": req.task, "round": req.round}

@router.get("/health")
async def health():
    return {"status": "ok"}
