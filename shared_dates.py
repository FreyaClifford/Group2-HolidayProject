"""
shared_dates.py
Call render_date_header() as the very first thing on every non-home page.
It renders the travel-dates bar above the page title and syncs with session state.
"""

import streamlit as st
from datetime import date, timedelta


def render_date_header():
    """
    Renders a compact travel-dates bar at the top of the page (above the title).
    Dates are shared across all pages via st.session_state.
    Returns (start, end, nights).
    """
    today = date.today()

    if "travel_start" not in st.session_state:
        st.session_state.travel_start = today + timedelta(days=7)
    if "travel_end" not in st.session_state:
        st.session_state.travel_end = today + timedelta(days=14)

    col1, col2, col3, col4 = st.columns([1.6, 1.6, 2.2, 1])

    with col1:
        start = st.date_input(
            "✈️ Departure",
            value=st.session_state.travel_start,
            min_value=today,
            key="date_header_start",
        )
    with col2:
        end = st.date_input(
            "🏠 Return",
            value=st.session_state.travel_end,
            min_value=today + timedelta(days=1),
            key="date_header_end",
        )
    with col3:
        if start >= end:
            st.error("Return must be after departure.")
            nights = 0
        else:
            nights = (end - start).days
            st.info(
                f"📅 **{nights} night{'s' if nights != 1 else ''}**  ·  "
                f"{start.strftime('%d %b')} → {end.strftime('%d %b %Y')}"
            )
    with col4:
        step = st.session_state.get("current_step", 1)
        labels = ["🌍 Destination", "🏨 Hotel", "📋 Review"]
        st.caption("Progress")
        for i, label in enumerate(labels):
            prefix = "▶" if i + 1 == step else "✓" if i + 1 < step else "·"
            st.caption(f"{prefix} {label}")

    st.session_state.travel_start = start
    st.session_state.travel_end = end

    st.divider()
    return start, end, nights
