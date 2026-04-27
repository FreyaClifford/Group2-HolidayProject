import streamlit as st
from datetime import date, timedelta
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_dates import render_date_header

st.set_page_config(page_title="📋 Trip Review", page_icon="📋", layout="wide")

st.session_state["current_step"] = 3

# ── Date header (above title) ─────────────────────────────────────────────────

start, end, nights = render_date_header()

# ── Page title ────────────────────────────────────────────────────────────────

st.title("📋 Trip Review")
st.caption("Everything in one place. Review your destination, hotel, and flight before you book.")

# ── Pull saved choices from session state ─────────────────────────────────────

city         = st.session_state.get("selected_city", None)
city_flag    = st.session_state.get("selected_city_flag", "🌍")
city_country = st.session_state.get("selected_city_country", "")
hotel        = st.session_state.get("selected_hotel", None)

st.divider()

# ── Three summary cards ───────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)

# ── Destination card ──────────────────────────────────────────────────────────
with col1:
    st.subheader("🌍 Destination")
    if city:
        st.markdown(f"## {city_flag} {city}")
        st.write(f"📍 {city_country}")
        if nights > 0:
            st.write(f"📅 {nights} night{'s' if nights != 1 else ''}")
            st.write(f"✈️ {start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}")
        st.success("Confirmed ✅")
    else:
        st.info("No destination selected yet.")
        st.page_link("pages/1_destination_selection.py", label="🌍 Pick a destination →")

# ── Hotel card ────────────────────────────────────────────────────────────────
with col2:
    st.subheader("🏨 Hotel")
    if hotel:
        st.markdown(f"## {hotel['name']}")
        st.write(f"📍 {hotel['address']}")
        st.write(f"⭐ {hotel['rating']} rating  ·  💰 {hotel['price_level']}")
        if hotel.get("website"):
            st.markdown(f"[🌐 Visit website]({hotel['website']})")
        st.success("Confirmed ✅")
    else:
        st.info("No hotel selected yet.")
        if city:
            st.page_link("pages/2_map.py", label="🏨 Find a hotel →")
        else:
            st.caption("Pick a destination first, then find a hotel.")

# ── Flight card (placeholder) ─────────────────────────────────────────────────
with col3:
    st.subheader("✈️ Flight")
    st.info("Flight booking coming soon — your team is working on this.")
    st.write("**From:** London (LON)")
    st.write(f"**To:** {city if city else '—'}")
    st.write(f"**Date:** {start.strftime('%d %b %Y') if start else '—'}")
    st.write(f"**Return:** {end.strftime('%d %b %Y') if end else '—'}")
    st.caption("Use the Flights page to search and book once you're ready.")
    st.page_link("pages/3_Flights_api.py", label="✈️ Search flights →")

st.divider()

# ── Full summary ──────────────────────────────────────────────────────────────

st.subheader("📝 Trip Summary")

summary_complete = city and hotel and nights > 0

if summary_complete:
    st.markdown(
        f"You're heading to **{city_flag} {city}, {city_country}** for **{nights} night{'s' if nights != 1 else ''}**, "
        f"departing **{start.strftime('%d %b %Y')}** and returning **{end.strftime('%d %b %Y')}**. "
        f"You'll be staying at **{hotel['name']}** ({hotel['rating']}⭐, {hotel['price_level']})."
    )
    st.success("Your trip is looking great! Book your flight to complete the plan.")
else:
    missing = []
    if not city:
        missing.append("a destination")
    if not hotel:
        missing.append("a hotel")
    if nights == 0:
        missing.append("valid travel dates")
    st.warning(f"Still to do: pick {', '.join(missing)}.")

st.divider()

# ── Edit links ────────────────────────────────────────────────────────────────

st.subheader("✏️ Make changes")
ec1, ec2, ec3 = st.columns(3)
with ec1:
    st.page_link("pages/1_destination_selection.py", label="🌍 Change destination")
with ec2:
    st.page_link("pages/2_map.py", label="🏨 Change hotel")
with ec3:
    st.page_link("pages/3_Flights_api.py", label="✈️ Search flights")
