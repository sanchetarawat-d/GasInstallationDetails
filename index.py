import streamlit as st
from datetime import datetime, timedelta
import re
import dateparser
import requests
import json

# --------------------------
# CONFIG (Secrets + Headers)
# --------------------------
BEARER_TOKEN = st.secrets["BEARER_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]
FOLDER_ID = st.secrets["FOLDER_ID"]  # integer
QUEUE_NAME = st.secrets["QUEUE_NAME"]

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

# --------------------------
# Reusable API Utilities
# --------------------------
def api_get(endpoint, params=None, folder_id=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = HEADERS.copy()
    if folder_id:
        headers["X-UiPath-OrganizationUnitId"] = str(folder_id)
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def api_post(endpoint, payload, folder_id=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = HEADERS.copy()
    if folder_id:
        headers["X-UiPath-OrganizationUnitId"] = str(folder_id)
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()

# --------------------------
# NLP Time Expression Parser
# --------------------------
def get_date_range_from_expression(expression: str):
    now = datetime.now()
    expression = expression.lower().strip()

    quarter_match = re.match(r"(1st|first|2nd|second|3rd|third|4th|fourth|q1|q2|q3|q4)\s*(quarter)?\s*(of|in)?\s*(\d{4})", expression)
    if quarter_match:
        quarter_map = {
            "1st": (1, 3), "first": (1, 3), "q1": (1, 3),
            "2nd": (4, 6), "second": (4, 6), "q2": (4, 6),
            "3rd": (7, 9), "third": (7, 9), "q3": (7, 9),
            "4th": (10, 12), "fourth": (10, 12), "q4": (10, 12)
        }
        q_key = quarter_match.group(1)
        year = int(quarter_match.group(4))
        start_month, end_month = quarter_map[q_key]
        start_date = datetime(year, start_month, 1)
        end_date = datetime(year, end_month + 1, 1) - timedelta(days=1) if end_month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
        return start_date.date(), end_date.date()

    if expression == "yesterday":
        d = now - timedelta(days=1)
        return d.date(), d.date()

    if expression == "today":
        return now.date(), now.date()

    if "last week" in expression:
        start = now - timedelta(days=now.weekday() + 7)
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "this week" in expression:
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "last month" in expression:
        first_this_month = now.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        start = last_month_end.replace(day=1)
        return start.date(), last_month_end.date()

    if "this month" in expression:
        start = now.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
        return start.date(), end.date()

    parsed = dateparser.parse(expression)
    if parsed:
        return parsed.date(), parsed.date()

    raise ValueError("❌ Could not parse date expression.")

# --------------------------
# Push to UiPath Queue
# --------------------------
def push_to_queue(start_date, end_date):
    payload = {
        "itemData": {
            "Name": QUEUE_NAME,
            "SpecificContent": {
                "StartDate": str(start_date),
                "EndDate": str(end_date)
            },
            "Priority": "Normal"
        }
    }
    result = api_post("odata/Queues/UiPathODataSvc.AddQueueItem", payload, folder_id=FOLDER_ID)
    return result

# --------------------------
# Chatbot UI
# --------------------------
st.set_page_config(page_title="📤 UiPath Queue Chatbot", layout="centered")
st.title("🤖 Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! 👋 Enter your querry for Gas Installations"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Enter your date expression...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        start, end = get_date_range_from_expression(user_input)
        push_to_queue(start, end)
        reply = f"✅ Dates sent to UiPath Queue!\n\n📅 **Start Date**: `{start}`\n📅 **End Date**: `{end}`"
    except Exception as e:
        reply = f"❌ Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
