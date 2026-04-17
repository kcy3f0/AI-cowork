import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
import sys
import os

# 將 api 目錄加入 sys.path 以便匯入 main, models, database
# 這是為了在沒有安裝為 package 的情況下也能執行測試
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db
import models

# --- 測試資料庫設定 ---
# 使用記憶體中的 SQLite 資料庫進行測試 (:memory:)
# StaticPool 用於確保所有連線都指向同一個記憶體資料庫
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 在測試開始前建立表格
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db_session():
    """
    提供一個乾淨的資料庫 Session 給每個測試案例。
    """
    # 建立一個新的 session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清除所有資料，確保測試隔離
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

@pytest.fixture
def client(db_session):
    """
    提供一個配置好 dependency_override 的 TestClient。
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_get_tasks_empty(client):
    """
    測試當沒有任何任務時，GET /tasks/ 應回傳空列表。
    """
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_tasks_success(client, db_session):
    """
    測試 GET /tasks/ 節點，確認是否能正確取得任務清單。
    """
    # 1. 準備測試資料
    task1 = models.Task(description="Test Task 1", status="Pending")
    task2 = models.Task(description="Test Task 2", status="Completed", result="Done")
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    # 2. 呼叫 API
    response = client.get("/tasks/")

    # 3. 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # 預期是倒序排列 (id desc)
    assert data[0]["description"] == "Test Task 2"
    assert data[1]["description"] == "Test Task 1"
    assert isinstance(data[0]["created_at"], str)

def test_get_tasks_pagination(client, db_session):
    """
    測試 GET /tasks/ 的分頁功能 (skip, limit)。
    """
    # 1. 建立 5 個任務
    for i in range(5):
        db_session.add(models.Task(description=f"Task {i}"))
    db_session.commit()

    # 2. 測試 limit=2
    response = client.get("/tasks/?limit=2")
    assert len(response.json()) == 2

    # 3. 測試 skip=3
    # 總共 5 個 (ID 1~5)，倒序為 5, 4, 3, 2, 1
    # skip 3 應該剩 2, 1
    response = client.get("/tasks/?skip=3")
    data = response.json()
    assert len(data) == 2
    assert data[0]["description"] == "Task 1"
    assert data[1]["description"] == "Task 0"
