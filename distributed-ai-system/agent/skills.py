import os
import requests
from typing import Optional, Dict, Any

class AgentSkills:
    """
    這個模組提供了一系列可以被 AI Agent (如 LangChain, AutoGen 等)
    當作「Skill」或「Tool」使用的函式。
    """
    def __init__(self, api_url: Optional[str] = None):
        # 如果沒有提供 API URL，則從環境變數讀取
        self.api_url = api_url or os.getenv("API_URL", "http://localhost:8000")

    def fetch_pending_task(self) -> Optional[Dict[str, Any]]:
        """
        Skill: 取得一個待處理的任務。
        如果沒有任務，回傳 None。

        回傳的字典結構範例:
        {
            "id": 1,
            "description": "幫我翻譯這段文字",
            "status": "Claimed",
            ...
        }
        """
        try:
            response = requests.get(f"{self.api_url}/tasks/pending", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"[AgentSkills] Error fetching task: {e}")
            return None

    def submit_task_result(self, task_id: int, result: str, status: str = "Completed") -> bool:
        """
        Skill: 提交任務的最終結果，並更新狀態。

        參數:
            task_id: 任務 ID
            result: 任務執行結果
            status: 狀態 (預設為 Completed，也可以是 Failed)

        回傳:
            True 表示成功，False 表示失敗
        """
        try:
            payload = {
                "status": status,
                "result": result
            }
            response = requests.put(f"{self.api_url}/tasks/{task_id}/status", json=payload, timeout=5)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"[AgentSkills] Error submitting task {task_id}: {e}")
            return False

# 提供一個全域實例，方便直接當作 function 呼叫
_default_skills = AgentSkills()

def fetch_task() -> Optional[Dict[str, Any]]:
    """LangChain / OpenAI Tool: 取得待處理的任務"""
    return _default_skills.fetch_pending_task()

def submit_result(task_id: int, result: str) -> bool:
    """LangChain / OpenAI Tool: 提交任務結果"""
    return _default_skills.submit_task_result(task_id, result)
