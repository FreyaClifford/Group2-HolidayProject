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
st.caption("Everything in one place. Review your destination, hotel, and flights before you book.")

# ── Pull saved choices from session state ─────────────────────────────────────

city         = st.session_state.get("selected_city", None)
city_flag    = st.session_state.get("selected_city_flag", "🌍")
city_country = st.session_state.get("selected_city_country", "")
hotel        = st.session_state.get("selected_hotel", None)
flights      = st.session_state.get("selected_flights", None)

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

# ── Flight card ───────────────────────────────────────────────────────────────
with col3:
    st.subheader("✈️ Flights")
    if flights:
        ob  = flights.get("outbound", {})
        ret = flights.get("return", {})
        curr = flights.get("currency", "GBP")

        st.markdown("**🛫 Outbound**")
        st.write(f"{ob.get('Starting Airport')} → {ob.get('Destination Airport')}")
        st.write(f"🕐 {ob.get('Departure')}")
        st.write(f"✈️ {ob.get('Airline')}  ·  {ob.get('Flight Number')}")
        st.write(f"💰 {curr} {ob.get('Price')}")

        st.markdown("**🛬 Return**")
        st.write(f"{ret.get('Starting Airport')} → {ret.get('Destination Airport')}")
        st.write(f"🕐 {ret.get('Departure')}")
        st.write(f"✈️ {ret.get('Airline')}  ·  {ret.get('Flight Number')}")
        st.write(f"💰 {curr} {ret.get('Price')}")

        st.success(f"Total: **{curr} {flights.get('total_price')}** ✅")
    else:
        st.info("No flights selected yet.")
        st.write(f"**From:** London (LON)")
        st.write(f"**To:** {city if city else '—'}")
        st.write(f"**Depart:** {start.strftime('%d %b %Y') if start else '—'}")
        st.write(f"**Return:** {end.strftime('%d %b %Y') if end else '—'}")
        st.page_link("pages/3_tickets.py", label="✈️ Search flights →")

st.divider()

# ── Full summary ──────────────────────────────────────────────────────────────

st.subheader("📝 Trip Summary")

summary_complete = city and hotel and nights > 0

if summary_complete:
    flight_line = (
        f" Your flights are booked with **{flights['outbound']['Airline']}** (outbound) "
        f"and **{flights['return']['Airline']}** (return), totalling "
        f"**{flights['currency']} {flights['total_price']}**."
        if flights else " Head to the flights page to complete your booking."
    )
    st.markdown(
        f"You're heading to **{city_flag} {city}, {city_country}** for "
        f"**{nights} night{'s' if nights != 1 else ''}**, "
        f"departing **{start.strftime('%d %b %Y')}** and returning **{end.strftime('%d %b %Y')}**. "
        f"You'll be staying at **{hotel['name']}** ({hotel['rating']}⭐, {hotel['price_level']})."
        + flight_line
    )
    if flights:
        st.success("🎉 Your trip is all planned! Click through to book your flights.")
    else:
        st.warning("Almost there — just find and select your flights to finish planning.")
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
    st.page_link("pages/3_tickets.py", label="✈️ Change flights")
