import streamlit as st

# 🔐 Simple password protection
st.set_page_config(page_title="Kitchen Dashboard", layout="wide")
PASSWORD = "chef2024"  # Change this to your secret

st.title("🔒 Kitchen Dashboard Login")

password_input = st.text_input("Enter password to continue:", type="password")
if password_input != PASSWORD:
    st.stop()

import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# File names
TASK_FILE = "Kitchen mise en place and cleaning tasks.csv"
VALIDATION_LOG = "Kitchen tasks validation.csv"

# Load task data
if os.path.exists(TASK_FILE):
    task_df = pd.read_csv(TASK_FILE)
else:
    st.error("Task file is missing.")
    st.stop()

# Today's date
today = date.today().strftime("%Y-%m-%d")

# Determine if task is due
def is_due(task_date, last_validated, frequency):
    if frequency == "daily":
        return True
    elif frequency == "weekly":
        if not last_validated or pd.isna(last_validated):
            return True
        return (pd.to_datetime(today) - pd.to_datetime(last_validated)).days >= 7
    return True

task_df["Is Due"] = task_df.apply(
    lambda row: is_due(row["Date"], row["Last Validated Date"], row["Frequency"]), axis=1
)
today_tasks = task_df[task_df["Is Due"] == True]

# Title
st.title("🍽️ Intelligent Kitchen Task Validator")
st.markdown(f"### 📅 Today's Date: {today}")

# Add a new task manually
st.subheader("➕ Add a New Task")
with st.form("add_task_form"):
    new_task_name = st.text_input("Task Name")
    new_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    new_target_time = st.number_input("Target Time (min)", min_value=1, step=1)
    submitted = st.form_submit_button("Add Task")
    if submitted:
        if new_task_name:
            new_row = {
                "Task Name": new_task_name,
                "Frequency": new_frequency,
                "Date": today,
                "Completed": False,
                "Cook Name": "",
                "Prep Time (min)": "",
                "Target Time (min)": new_target_time,
                "Efficiency (%)": "",
                "Performance Tag": "",
                "Last Validated Date": "",
                "Is Due": True
            }
            task_df = pd.concat([task_df, pd.DataFrame([new_row])], ignore_index=True)
            task_df.to_csv(TASK_FILE, index=False)
            st.success(f"Added task: {new_task_name}")
        else:
            st.warning("Please enter a task name.")

# Display tasks
if today_tasks.empty:
    st.info("No tasks due today.")
else:
    for i, row in today_tasks.iterrows():
        task = row["Task Name"]
        idx = row.name
        task_date = row["Date"]
        target_time = row["Target Time (min)"]

        st.markdown(f"""---
### {task}
📅 Due: **{task_date}**  
🎯 Target Time: **{target_time} min**""")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            cook = st.text_input("Cook Name", key=f"cook_{i}")
        with col2:
            time_spent = st.number_input("Prep Time (min)", min_value=1, step=1, key=f"time_{i}")
        with col3:
            validate = st.button("✅ Validate", key=f"validate_{i}")

        if validate:
            if not cook:
                st.warning("Please enter the cook's name.")
                continue

            if os.path.exists(VALIDATION_LOG):
                log_df = pd.read_csv(VALIDATION_LOG, on_bad_lines='skip', engine='python')
                duplicate = ((log_df["Task Name"] == task) & 
                             (log_df["Date"] == today) & 
                             (log_df["Cook Name"] == cook)).any()
                if duplicate:
                    st.warning(f"{task} already validated by {cook} today.")
                    continue

            task_df.at[idx, "Completed"] = True
            task_df.at[idx, "Cook Name"] = cook
            task_df.at[idx, "Prep Time (min)"] = time_spent
            efficiency = min(100, int((target_time / time_spent) * 100))
            tag = "🟢" if efficiency >= 90 else "🟡" if efficiency >= 70 else "🔴"
            task_df.at[idx, "Efficiency (%)"] = efficiency
            task_df.at[idx, "Performance Tag"] = tag
            task_df.at[idx, "Date"] = today
            task_df.at[idx, "Last Validated Date"] = today
            task_df.to_csv(TASK_FILE, index=False)

            log_entry = {
                "Task Name": task,
                "Date": today,
                "Cook Name": cook,
                "Prep Time (min)": time_spent,
                "Target Time (min)": target_time,
                "Efficiency (%)": efficiency,
                "Performance Tag": tag,
                "Validation Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            log_df = pd.DataFrame([log_entry])
            if os.path.exists(VALIDATION_LOG):
                log_df.to_csv(VALIDATION_LOG, mode='a', header=False, index=False)
            else:
                log_df.to_csv(VALIDATION_LOG, index=False)

            st.success(f"✅ {task} validated by {cook} ({efficiency}% {tag})")

# Validation Log Viewer
st.subheader("📊 Validation Log")

try:
    log_view = pd.read_csv(VALIDATION_LOG, on_bad_lines='skip', engine='python')
    log_view.dropna(how="all", inplace=True)
    log_view.dropna(axis=1, how="all", inplace=True)

    expected_cols = [
        "Task Name", "Date", "Cook Name", "Prep Time (min)",
        "Target Time (min)", "Efficiency (%)", "Performance Tag", "Validation Time"
    ]
    log_view = log_view[[col for col in expected_cols if col in log_view.columns]]
    log_view = log_view.astype(str).reset_index(drop=True)

    # Render as markdown table
    if not log_view.empty:
        markdown = "| " + " | ".join(log_view.columns) + " |\n"
        markdown += "| " + " | ".join(["---"] * len(log_view.columns)) + " |\n"
        for _, row in log_view.iterrows():
            markdown += "| " + " | ".join(row.values) + " |\n"
        st.markdown(markdown)
    else:
        st.info("Validation log is empty.")

except Exception as e:
    st.error(f"⚠️ Could not load validation log: {e}")
