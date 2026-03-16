import streamlit as st
import requests
import os
from streamlit_autorefresh import st_autorefresh

# 設定 Streamlit 頁面
st.set_page_config(page_title="AI Agent 控制台", page_icon="🤖", layout="wide")

# 從環境變數讀取後端 API 網址，預設為本機開發使用
API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_tasks():
    """從 FastAPI 取得所有任務的列表"""
    try:
        response = requests.get(f"{API_URL}/tasks/", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"無法連線至 API: {e}")
        return []

def submit_task(description: str):
    """向 FastAPI 提交新任務"""
    try:
        response = requests.post(f"{API_URL}/tasks/", json={"description": description}, timeout=5)
        response.raise_for_status()
        st.success("任務已成功提交至佇列！")
    except requests.exceptions.RequestException as e:
        st.error(f"提交任務失敗: {e}")

# 自動刷新邏輯
# 預設每 3 秒 (3000 ms) 自動重繪一次頁面，以達到即時更新效果
count = st_autorefresh(interval=3000, limit=1000, key="data_refresh")

# === UI 配置開始 ===
st.title("🤖 分散式 AI 代理人協作系統控制台")
st.markdown("在這裡，您可以提交任務給後端的 AI 代理人，並即時查看處理狀態與最終結果。")

# 1. 任務提交區塊
st.subheader("📝 建立新任務")
with st.form("new_task_form", clear_on_submit=True):
    task_desc = st.text_area("輸入任務描述：", placeholder="例如：幫我將這段英文翻譯成繁體中文...", height=100)
    submitted = st.form_submit_button("送出任務")
    if submitted and task_desc.strip():
        submit_task(task_desc.strip())

# 2. 任務狀態列表區塊
st.subheader("📋 任務執行狀態")

# 使用 Streamlit 的 placeholder 來實現自動更新
placeholder = st.empty()

# 取得任務並顯示
tasks = get_tasks()

if not tasks:
    placeholder.info("目前系統中沒有任何任務。")
else:
    # 顯示任務列表 (可以用表格或展開卡片)
    with placeholder.container():
        # 計算統計資料
        total = len(tasks)
        pending = sum(1 for t in tasks if t["status"] == "Pending")
        claimed = sum(1 for t in tasks if t["status"] == "Claimed")
        completed = sum(1 for t in tasks if t["status"] == "Completed")
        failed = sum(1 for t in tasks if t["status"] == "Failed")

        # 顯示統計指標
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("總任務數", total)
        col2.metric("待處理 (Pending)", pending)
        col3.metric("處理中 (Claimed)", claimed)
        col4.metric("已完成 (Completed)", completed)

        st.divider()

        # 顯示任務詳情
        for task in tasks:
            status = task["status"]
            # 設定不同狀態的顏色標籤
            status_color = "gray"
            if status == "Pending":
                status_color = "orange"
            elif status == "Claimed":
                status_color = "blue"
            elif status == "Completed":
                status_color = "green"
            elif status == "Failed":
                status_color = "red"

            with st.expander(f"任務 #{task['id']} - [{status}] {task['description'][:30]}..."):
                st.markdown(f"**狀態:** :{status_color}[{status}]")
                st.markdown(f"**任務內容:**\n{task['description']}")
                st.markdown(f"**建立時間:** {task['created_at']}")

                if task["result"]:
                    st.markdown("---")
                    st.markdown("**執行結果:**")
                    st.success(task["result"])
                elif status == "Failed":
                    st.markdown("---")
                    st.markdown("**錯誤訊息:**")
                    st.error(task.get("result", "未知錯誤"))

# 3. 狀態提示
if st.button("🔄 手動刷新資料"):
    st.rerun()

st.caption(f"提示：畫面每 3 秒會自動刷新最新狀態。API 狀態: {'連線成功' if tasks is not None else '離線'}")
