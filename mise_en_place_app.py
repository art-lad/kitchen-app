import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
# --- SAFE RERUN TRIGGER ---
if st.session_state.get("triggered", False):
    st.session_state["triggered"] = False
    st.experimental_rerun()
# ---- PAGE CONFIG ----
st.set_page_config(page_title="Quinta Pupusas - Kitchen Dashboard", layout="wide")
# ---- AUTH SETUP ----
AUTHORIZED_USERS = {
    "Carlos": "tacos123",
    "Luz": "guac456",
    "Isaac": "hot789"
}
TASK_FILE = "Kitchen mise en place and cleaning tasks.csv"
VALIDATION_LOG = "Kitchen tasks validation.csv"
# ---- SESSION SETUP ----
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["cook_name"] = None
# ---- LOGIN BLOCK ----
if not st.session_state["authenticated"]:
    st.title("🔐 Staff Login")
    cook_name = st.selectbox("Select your name:", list(AUTHORIZED_USERS.keys()))
    password = st.text_input("Enter your password:", type="password")
    if password:
if password == AUTHORIZED_USERS.get(cook_name):
    st.session_state["authenticated"] = True
    st.session_state["cook_name"] = cook_name
    st.session_state["triggered"] = True
    st.success(f"✅ Welcome, {cook_name} 👋")
    st.stop()
        else:
# ---- MAIN APP (only if authenticated) ----
if st.session_state["authenticated"]:
    cook_name = st.session_state.get("cook_name", "Unknown")
    today = date.today().strftime("%Y-%m-%d")
    # LOGOUT
    if st.button("Logout"):
    # HEADER
    # LOAD TASKS
    if os.path.exists(TASK_FILE):
        task_df = pd.read_csv(TASK_FILE)
    else:
    def is_due(task_date, last_validated, freq):
        if freq == "daily":
            return True
        elif freq == "weekly":
            if not last_validated or pd.isna(last_validated):
                return True
            return (pd.to_datetime(date.today()) - pd.to_datetime(last_validated)).days >= 7
        return True
    task_df["Is Due"] = task_df.apply(
        lambda row: is_due(row["Date"], row["Last Validated Date"], row["Frequency"]), axis=1
    )
    today_tasks = task_df[task_df["Is Due"] == True]
    # ADD TASK
    with st.form("add_task"):
        new_task = st.text_input("Task Name")
        new_freq = st.selectbox("Frequency", ["once", "daily", "weekly"])
        new_target = st.number_input("Target Time (min)", min_value=1, step=1)
        add_submit = st.form_submit_button("Add Task")
        if add_submit and new_task:
            new_row = {
                "Task Name": new_task,
                "Frequency": new_freq,
                "Date": today,
                "Completed": False,
                "Cook Name": "",
                "Prep Time (min)": "",
                "Target Time (min)": new_target,
                "Efficiency (%)": "",
                "Performance Tag": "",
                "Last Validated Date": "",
                "Is Due": True
            }
            task_df = pd.concat([task_df, pd.DataFrame([new_row])], ignore_index=True)
            task_df.to_csv(TASK_FILE, index=False)
    # SHOW TASKS
    if today_tasks.empty:
    else:
        for i, row in today_tasks.iterrows():
            task = row["Task Name"]
            idx = row.name
            col1, col2 = st.columns([1, 1])
            with col1:
                prep_time = st.number_input("Prep Time (min)", min_value=1, step=1, key=f"prep_{i}")
            with col2:
                validate = st.button("✅ Validate", key=f"val_{i}")
            if validate:
                if os.path.exists(VALIDATION_LOG):
                    log_df = pd.read_csv(VALIDATION_LOG, on_bad_lines='skip', engine='python')
                    is_dup = (
                        (log_df["Task Name"] == task) &
                        (log_df["Date"] == today) &
                        (log_df["Cook Name"] == cook_name)
                    ).any()
                    if is_dup:
                        continue
                efficiency = min(100, int((row["Target Time (min)"] / prep_time) * 100))
                tag = "🟢" if efficiency >= 90 else "🟡" if efficiency >= 70 else "🔴"
                task_df.at[idx, "Completed"] = True
                task_df.at[idx, "Cook Name"] = cook_name
                task_df.at[idx, "Prep Time (min)"] = prep_time
                task_df.at[idx, "Efficiency (%)"] = efficiency
                task_df.at[idx, "Performance Tag"] = tag
                task_df.at[idx, "Date"] = today
                task_df.at[idx, "Last Validated Date"] = today
                task_df.to_csv(TASK_FILE, index=False)
                log_entry = pd.DataFrame([{
                    "Task Name": task,
                    "Date": today,
                    "Cook Name": cook_name,
                    "Prep Time (min)": prep_time,
                    "Target Time (min)": row["Target Time (min)"],
                    "Efficiency (%)": efficiency,
                    "Performance Tag": tag,
                    "Validation Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                if os.path.exists(VALIDATION_LOG):
                    log_entry.to_csv(VALIDATION_LOG, mode='a', header=False, index=False)
                else:
                    log_entry.to_csv(VALIDATION_LOG, index=False)
    # VALIDATION LOG
    try:
        log_df = pd.read_csv(VALIDATION_LOG, on_bad_lines='skip', engine='python')
        log_df.dropna(how="all", inplace=True)
        log_df.dropna(axis=1, how="all", inplace=True)
    except Exception as e:

