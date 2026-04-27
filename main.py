import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="🌴 Holiday Planner", page_icon="🌴", layout="wide")

# ── Hero ──────────────────────────────────────────────────────────────────────

st.title("🌴 Holiday Planner")
st.subheader("Your personal travel companion — from destination to doorstep.")
st.markdown(
    "Planning a holiday shouldn't be stressful. Set your travel dates, pick your destination, "
    "find a hotel, and book your flight — all in one place."
)

st.divider()

# ── How it works ──────────────────────────────────────────────────────────────

st.subheader("How it works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🌍 1. Pick a destination")
    st.markdown(
        "Compare cities side-by-side using live weather forecasts. "
        "Filter by vibe — beach, nightlife, culture, budget-friendly and more — "
        "then let the weather scorer rank them for your exact travel window."
    )

with col2:
    st.markdown("### 🏨 2. Find your hotel")
    st.markdown(
        "Once you've chosen a destination, search for hotels, nightclubs, "
        "and activities using live data. Filter by rating and price level, "
        "and see every result pinned on an interactive map."
    )

with col3:
    st.markdown("### ✈️ 3. Book your flight")
    st.markdown(
        "Search live, low-cost flights from London to your chosen destination. "
        "Filter by direct-only, pick your currency, and jump straight to booking "
        "with a single click."
    )

st.divider()

# ── Date setup ────────────────────────────────────────────────────────────────

st.subheader("📅 When are you travelling?")
st.caption("Set your dates here — they'll carry through to every page automatically.")

today = date.today()

if "travel_start" not in st.session_state:
    st.session_state.travel_start = today + timedelta(days=7)
if "travel_end" not in st.session_state:
    st.session_state.travel_end = today + timedelta(days=14)

col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    start = st.date_input(
        "✈️ Departure",
        value=st.session_state.travel_start,
        min_value=today,
        key="home_start",
    )
with col2:
    end = st.date_input(
        "🏠 Return",
        value=st.session_state.travel_end,
        min_value=today + timedelta(days=1),
        key="home_end",
    )
with col3:
    if start >= end:
        st.error("Return date must be after departure.")
    else:
        nights = (end - start).days
        st.info(
            f"📅 **{nights} night{'s' if nights != 1 else ''}** · "
            f"{start.strftime('%d %b')} → {end.strftime('%d %b %Y')}"
        )

st.session_state.travel_start = start
st.session_state.travel_end   = end

st.divider()

# ── CTA ───────────────────────────────────────────────────────────────────────

if start < end:
    st.subheader("Ready? Let's find your destination.")
    st.page_link("pages/1_destination_selection.py", label="🌍 Compare destinations →")
