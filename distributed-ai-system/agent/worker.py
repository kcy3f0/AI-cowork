import time
import os
import random
from skills import fetch_task, submit_result

def simulate_ai_processing(task_description: str) -> str:
    """
    模擬 AI 思考與處理的過程。
    在這裡，您可以替換成真實的 LLM 呼叫 (如 OpenAI API)。
    """
    print(f"🧠 [AI] 正在思考如何處理任務: '{task_description}'...")
    # 模擬 3 到 8 秒的處理時間
    process_time = random.uniform(3, 8)
    time.sleep(process_time)

    # 回傳假造的處理結果
    return f"這是我 (AI Agent) 處理完 '{task_description}' 的結果！(耗時 {process_time:.1f} 秒)"

def main():
    print("🤖 Agent Worker 啟動，開始監聽中央佇列...")
    api_url = os.getenv("API_URL", "http://localhost:8000")
    print(f"🔗 連線的 API 網址: {api_url}")

    while True:
        # 1. 嘗試抓取任務
        task = fetch_task()

        if task is None:
            # 如果沒有任務，等待一段時間後重試
            print("💤 目前沒有待處理的任務，休息 3 秒鐘...")
            time.sleep(3)
            continue

        # 2. 如果有任務，開始處理
        task_id = task["id"]
        description = task["description"]
        print(f"\n✅ 成功認領任務 #{task_id} (狀態更新為 Claimed)")
        print(f"📝 任務內容: {description}")

        try:
            # 執行 AI 邏輯
            result = simulate_ai_processing(description)

            # 3. 處理完成，回報結果
            success = submit_result(task_id=task_id, result=result)
            if success:
                print(f"🎉 任務 #{task_id} 處理完成，結果已成功回報！")
            else:
                print(f"❌ 任務 #{task_id} 處理完成，但回報結果時發生錯誤。")

        except Exception as e:
            print(f"🚨 處理任務 #{task_id} 時發生未預期錯誤: {e}")
            # 如果發生錯誤，嘗試回報為 Failed
            submit_result(task_id=task_id, result=str(e), status="Failed")

if __name__ == "__main__":
    # 若 API_URL 未設定，嘗試等待幾秒讓後端啟動
    time.sleep(2)
    main()
