# pip install streamlit dateparser

import streamlit as st
from datetime import datetime, timedelta
import re
import dateparser

# -------------------------------
# Time expression parser function
# -------------------------------
def get_date_range_from_expression(expression: str):
    now = datetime.now()
    expression = expression.lower().strip()

    # Quarter-based expressions
    quarter_match = re.match(r"(1st|first|2nd|second|3rd|third|4th|fourth|q1|q2|q3|q4)\s*(quarter)?\s*(of|in)?\s*(\d{4})", expression)
    if quarter_match:
        quarter_map = {
            "1st": (1, 3), "first": (1, 3), "q1": (1, 3),
            "2nd": (4, 6), "second": (4, 6), "q2": (4, 6),
            "3rd": (7, 9), "third": (7, 9), "q3": (7, 9),
            "4th": (10, 12), "fourth": (10, 12), "q4": (10, 12)
        }
        quarter_key = quarter_match.group(1)
        year = int(quarter_match.group(4))
        start_month, end_month = quarter_map[quarter_key]
        start_date = datetime(year, start_month, 1)
        end_date = datetime(year, end_month + 1, 1) - timedelta(days=1) if end_month < 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
        return start_date.date(), end_date.date()

    # Week/month expressions
    if expression == "yesterday":
        d = now - timedelta(days=1)
        return d.date(), d.date()

    if expression == "today":
        d = now
        return d.date(), d.date()

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
        end = last_month_end
        return start.date(), end.date()

    if "this month" in expression:
        start = now.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
        return start.date(), end.date()

    # Fallback to parsing single date
    start = dateparser.parse(expression)
    if start:
        return start.date(), start.date()

    # If nothing matches
    raise ValueError("❌ Couldn't parse the expression. Try 'Q2 2024', 'last month', 'today', etc.")

# -------------------------------
# Streamlit Chatbot UI
# -------------------------------
st.set_page_config(page_title="🧠 Date Expression Chatbot", layout="centered")
st.title("🧠 Natural Language Date Chatbot")

# Session state to track messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! 🤖 Enter a time expression like **'last week'**, **'Q1 2024'**, or **'10 July 2025'** and I'll tell you the date range."}
    ]

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input from user
user_input = st.chat_input("Enter time frame expression...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        start_date, end_date = get_date_range_from_expression(user_input)
        response = f"✅ Start Date: **{start_date}**\n\n✅ End Date: **{end_date}**"
    except ValueError as e:
        response = str(e)

    # Show assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
