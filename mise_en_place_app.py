import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Task Manager", layout="wide")

# --- MANUAL NAME ENTRY ---
st.title("Task Manager")
cook_name = st.text_input("Enter your name to continue:")
if not cook_name:
    st.stop()

if st.button("Logout"):
    st.experimental_rerun()

# --- FILE PATHS ---
TASK_FILE = "Kitchen mise en place and cleaning tasks.csv"
VALIDATION_LOG = "Kitchen tasks validation.csv"
today = date.today().strftime("%Y-%m-%d")

# --- LOAD TASKS ---
if os.path.exists(TASK_FILE):
    task_df = pd.read_csv(TASK_FILE)
else:
    st.warning("⚠️ Task file not found.")
    st.stop()

# --- FILTER TASKS DUE ---
def is_due(task_date, last_validated, frequency):
    if frequency == "daily":
        return True
    elif frequency == "weekly":
        if not last_validated or pd.isna(last_validated):
            return True
        return (pd.to_datetime(date.today()) - pd.to_datetime(last_validated)).days >= 7
    return True

task_df["Is Due"] = task_df.apply(
    lambda row: is_due(row["Date"], row["Last Validated Date"], row["Frequency"]), axis=1
)
today_tasks = task_df[task_df["Is Due"] == True]

# --- GROUP TASKS BY DATE ---
grouped_tasks = task_df[
    (task_df["Is Due"] == True) &
    (task_df["Completed"] != True)
].groupby("Date")

st.markdown("## ✅ Tasks To Be Completed")

if grouped_tasks.ngroups == 0:
    st.info("🎉 No pending tasks due at the moment.")
else:
    for task_date, group in grouped_tasks:
        st.markdown(f"### 📅 Tasks for {task_date}")

        for i, row in group.iterrows():
            task = row["Task Name"]
            idx = row.name
            target_time = row["Target Time (min)"]

            # Make it compact on one line
            st.markdown(f"**{task}** — 🎯 {target_time} min")

            col1, col2 = st.columns([1, 1])
            with col1:
                time_spent = st.number_input(
                    "Prep Time (min)", min_value=1, step=1, key=f"time_{i}"
                )
            with col2:
                validate = st.button("✅ Validate", key=f"validate_{i}")

            if validate:
                if os.path.exists(VALIDATION_LOG):
                    log_df = pd.read_csv(VALIDATION_LOG, on_bad_lines='skip', engine='python')
                    duplicate = (
                        (log_df["Task Name"] == task) &
                        (log_df["Date"] == task_date)
                    ).any()
                    if duplicate:
                        st.warning(f"Task '{task}' already validated for {task_date}.")
                        continue

                task_df.at[idx, "Completed"] = True
                task_df.at[idx, "Prep Time (min)"] = time_spent
                efficiency = min(100, int((target_time / time_spent) * 100))
                tag = "🟢" if efficiency >= 90 else "🟡" if efficiency >= 70 else "🔴"
                task_df.at[idx, "Efficiency (%)"] = efficiency
                task_df.at[idx, "Performance Tag"] = tag
                task_df.at[idx, "Last Validated Date"] = today
                task_df.to_csv(TASK_FILE, index=False)

                log_entry = {
                    "Task Name": task,
                    "Date": task_date,
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

                st.success(f"✅ {task} validated ({efficiency}% {tag}) for {task_date}")
                st.experimental_rerun()  # Refresh view


# --- ADD TASK ---
st.subheader("➕ Add a New Task")
with st.form("add_task_form"):
    new_task_name = st.text_input("Task Name")
    new_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    new_target_time = st.number_input("Target Time (min)", min_value=1, step=1)
    submitted = st.form_submit_button("Add Task")
    if submitted and new_task_name:
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
        st.success(f"✅ Task added: {new_task_name}")


# --- VALIDATION LOG ---
st.markdown("### 📊 Validation Log")
try:
    log_view = pd.read_csv(VALIDATION_LOG, on_bad_lines='skip', engine='python')
    log_view.dropna(how="all", inplace=True)
    log_view.dropna(axis=1, how="all", inplace=True)
    st.dataframe(log_view)
except Exception as e:
    st.error(f"⚠️ Could not load validation log: {e}")
