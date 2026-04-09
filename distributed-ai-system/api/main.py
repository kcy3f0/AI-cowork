from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from celery import Celery

import models
from database import engine, get_db

# 建立資料庫表格
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Distributed AI Agent System API")

# --- Celery 設定 ---
# 安全性增強：Redis 連線現在支援身份驗證。
# 在生產環境中，請透過環境變數 REDIS_URL 提供包含密碼的連線字串。
# 格式範例：redis://:your_password@localhost:6379/0
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(name="agent_task_queue")
def agent_task_queue(task_id: int, description: str):
    """
    這是一個在 Celery Worker 中執行的虛擬函式。
    實際上，Agent 會直接從 API 抓取工作，或透過 Celery 的 Broker 消費佇列。
    在這個設計中，Celery Worker 主要負責管理重試或超時機制（如果需要），
    但在 MVP 裡，我們僅將任務推進 Queue。
    """
    pass

# --- Pydantic Schema ---
class TaskCreate(BaseModel):
    description: str

class TaskStatusUpdate(BaseModel):
    status: str # "Claimed" or "Completed" or "Failed"
    result: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    description: str
    status: str
    result: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# --- API Endpoints ---
@app.post("/tasks/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """
    Dashboard 建立新任務。
    任務會先寫入 SQLite (狀態: Pending)，
    然後推送到 Celery/Redis Queue 中。
    """
    db_task = models.Task(description=task.description, status="Pending")
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 將任務推入 Celery Queue
    # Agent 可以直接從 API 拿工作，或者連接到 Redis 消費
    # 這裡我們推播到一個名為 agent_task_queue 的 Celery 任務中
    try:
        celery_app.send_task('agent_task_queue', args=[db_task.id, db_task.description])
    except Exception as e:
        print(f"Error sending task to Celery: {e}")

    db_task.created_at = db_task.created_at.isoformat()
    db_task.updated_at = db_task.updated_at.isoformat()
    return db_task

@app.get("/tasks/", response_model=List[TaskResponse])
def get_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Dashboard 取得所有任務的清單。
    """
    tasks = db.query(models.Task).order_by(models.Task.id.desc()).offset(skip).limit(limit).all()
    # Pydantic 驗證 datetime 需要轉為 string 或用 jsonable_encoder
    for t in tasks:
        t.created_at = t.created_at.isoformat()
        t.updated_at = t.updated_at.isoformat()
    return tasks

@app.get("/tasks/pending", response_model=Optional[TaskResponse])
def get_pending_task(db: Session = Depends(get_db)):
    """
    Agent 主動來抓取 Pending 的任務。
    為避免 Race Condition，這裡可以用簡單的鎖，
    或是直接用一筆更新為 Claimed 狀態的 Query。
    """
    # 尋找第一筆 Pending 的任務
    task = db.query(models.Task).filter(models.Task.status == "Pending").first()
    if not task:
        return None

    # 標記為 Claimed
    task.status = "Claimed"
    db.commit()
    db.refresh(task)

    task.created_at = task.created_at.isoformat()
    task.updated_at = task.updated_at.isoformat()

    return task

@app.put("/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status(task_id: int, status_update: TaskStatusUpdate, db: Session = Depends(get_db)):
    """
    Agent 回報任務狀態與結果。
    """
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = status_update.status
    if status_update.result is not None:
        task.result = status_update.result

    db.commit()
    db.refresh(task)

    task.created_at = task.created_at.isoformat()
    task.updated_at = task.updated_at.isoformat()
    return task

@app.get("/health")
def health_check():
    return {"status": "ok"}
