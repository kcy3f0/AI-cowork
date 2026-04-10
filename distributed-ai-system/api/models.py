from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False) # 任務描述
    status = Column(String, default="Pending")  # Pending, Claimed, Completed, Failed
    result = Column(Text, nullable=True)       # 最終執行結果
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC).replace(tzinfo=None), onupdate=lambda: datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
