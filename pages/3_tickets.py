import requests
import os
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_dates import render_date_header

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="✈️ Search Flights", page_icon="✈️", layout="wide")

st.session_state["current_step"] = 3

# ── Date header (above title) ─────────────────────────────────────────────────

start, end, nights = render_date_header()

# ── Page title ────────────────────────────────────────────────────────────────

st.title("✈️ Search Flights")
st.caption("Search for low-cost flights from London to your chosen destination — outbound and return.")

st.divider()

# ── Constants ─────────────────────────────────────────────────────────────────

TOKEN    = "09e2f28e8bb7c3afdd252db783410cae"
BASE_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

CITY_IATA = {
    "Bali":           "DPS",
    "Jakarta":        "CGK",
    "Lombok":         "LOP",
    "Rio de Janeiro": "GIG",
    "Florianópolis":  "FLN",
    "Salvador":       "SSA",
    "Barcelona":      "BCN",
    "Seville":        "SVQ",
    "Mallorca":       "PMI",
    "Bangkok":        "BKK",
    "Cartagena":      "CTG",
    "Tenerife":       "TFS",
    "Phuket":         "HKT",
    "Maldives":       "MLE",
    "Lisbon":         "LIS",
    "Zanzibar":       "ZNZ",
}

CURRENCIES = [
    ("GBP", "🇬🇧 British Pound (GBP)"),
    ("USD", "🇺🇸 US Dollar (USD)"),
    ("EUR", "🇪🇺 Euro (EUR)"),
    ("AUD", "🇦🇺 Australian Dollar (AUD)"),
    ("CAD", "🇨🇦 Canadian Dollar (CAD)"),
    ("JPY", "🇯🇵 Japanese Yen (JPY)"),
    ("SGD", "🇸🇬 Singapore Dollar (SGD)"),
    ("AED", "🇦🇪 UAE Dirham (AED)"),
    ("THB", "🇹🇭 Thai Baht (THB)"),
    ("INR", "🇮🇳 Indian Rupee (INR)"),
]
CURRENCY_CODES  = [c[0] for c in CURRENCIES]
CURRENCY_LABELS = [c[1] for c in CURRENCIES]

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_flights(origin: str, destination: str, departure_date: str, currency: str, direct: bool) -> list[dict]:
    params = {
        "origin":       origin.upper(),
        "destination":  destination.upper(),
        "departure_at": departure_date,
        "one_way":      "true",
        "direct":       "true" if direct else "false",
        "sorting":      "price",
        "currency":     currency.upper(),
        "limit":        10,
        "page":         1,
        "token":        TOKEN,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    if not resp.text.strip():
        return []
    return resp.json().get("data", [])


def parse_flights(raw: list[dict], currency: str) -> pd.DataFrame:
    rows = []
    for item in raw:
        raw_dep = item.get("departure_at")
        dep_fmt = datetime.fromisoformat(raw_dep).strftime("%d %b %Y  %H:%M") if raw_dep else "Unknown"
        rows.append({
            "Starting Airport":    item.get("origin_airport"),
            "Destination Airport": item.get("destination_airport"),
            "Price":               item.get("price"),
            "Airline":             item.get("airline"),
            "Departure":           dep_fmt,
            "Transfers":           item.get("transfers"),
            "Flight Number":       item.get("flight_number"),
            "Duration (hrs)":      int(round((item.get("duration_to") or 0) / 60)),
            "Link":                "https://www.aviasales.com" + str(item.get("link") or ""),
            "_currency":           currency,
        })
    return pd.DataFrame(rows)


def render_flight_cards(df: pd.DataFrame, section_key: str):
    """Render flight result cards. Saves selection to session state on click."""
    if df.empty:
        st.warning("No flights matched your search. Try removing the direct-only filter or adjusting the date.")
        return

    currently_selected = st.session_state.get(f"selected_{section_key}", {}).get("Flight Number")

    for i, row in df.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])

            with c1:
                is_sel = currently_selected == row["Flight Number"]
                st.markdown(f"{'✅ ' if is_sel else ''}**{row['Starting Airport']} → {row['Destination Airport']}**")
                st.caption(f"✈️ {row['Airline']}  ·  Flight {row['Flight Number']}")
                st.write(f"🕐 Departs: **{row['Departure']}**")
                st.write(f"🔁 Transfers: {row['Transfers']}  ·  ⏱️ ~{row['Duration (hrs)']} hrs")

            with c2:
                st.metric("Price", f"{row['_currency']} {row['Price']}")

            with c3:
                st.link_button("🌐 Book now", row["Link"])
                btn_label = "✅ Selected" if is_sel else "Select this flight"
                if st.button(btn_label, key=f"btn_{section_key}_{i}", disabled=is_sel):
                    st.session_state[f"selected_{section_key}"] = row.to_dict()
                    st.rerun()

            st.divider()


# ── Search criteria ───────────────────────────────────────────────────────────

st.subheader("🔍 Search Criteria")

saved_city = st.session_state.get("selected_city", "")

city_options = [""] + list(CITY_IATA.keys()) + ["Other (enter IATA code manually)"]
saved_idx    = city_options.index(saved_city) if saved_city in city_options else 0

col1, col2 = st.columns(2)

with col1:
    chosen_city = st.selectbox(
        "🌍 Destination city",
        options=city_options,
        index=saved_idx,
        format_func=lambda c: (
            "— Select a city —" if c == ""
            else f"{c}  ({CITY_IATA[c]})" if c in CITY_IATA
            else c
        ),
    )

    if chosen_city == "Other (enter IATA code manually)":
        dest_iata = st.text_input("IATA airport / city code", placeholder="e.g. ORD, SYD, DXB").strip().upper()
    elif chosen_city and chosen_city in CITY_IATA:
        dest_iata = CITY_IATA[chosen_city]
        st.caption(f"IATA code: **{dest_iata}**")
    else:
        dest_iata = ""

with col2:
    currency_sel = st.selectbox(
        "💰 Currency",
        options=CURRENCY_CODES,
        index=0,
        format_func=lambda c: CURRENCY_LABELS[CURRENCY_CODES.index(c)],
    )
    direct_bool = st.radio("🛫 Direct flights only?", ["Yes", "No"], horizontal=True)
    direct = direct_bool == "Yes"

st.info(
    f"📅 Using your saved travel dates:  "
    f"**Outbound** {start.strftime('%d %b %Y')}  ·  **Return** {end.strftime('%d %b %Y')}  "
    f"({nights} night{'s' if nights != 1 else ''})"
)

search_clicked = st.button("🔍 Search flights", type="primary", disabled=(not dest_iata))

if not dest_iata:
    st.caption("Select a destination above to enable search.")

# ── Store search results in session state so they survive reruns ──────────────

if search_clicked and dest_iata:
    with st.spinner(f"Searching outbound flights to {dest_iata}…"):
        outbound_raw = fetch_flights("LON", dest_iata, start.isoformat(), currency_sel, direct)
        st.session_state["_outbound_df"]      = parse_flights(outbound_raw, currency_sel)
        st.session_state["_outbound_label"]   = f"London → {dest_iata}  ·  {start.strftime('%d %b %Y')}"

    with st.spinner(f"Searching return flights from {dest_iata}…"):
        return_raw = fetch_flights(dest_iata, "LON", end.isoformat(), currency_sel, direct)
        st.session_state["_return_df"]        = parse_flights(return_raw, currency_sel)
        st.session_state["_return_label"]     = f"{dest_iata} → London  ·  {end.strftime('%d %b %Y')}"

    # Store dest_iata and city for use in summary block below
    st.session_state["_last_dest_iata"] = dest_iata
    st.session_state["_last_dest_city"] = chosen_city if chosen_city not in ("", "Other (enter IATA code manually)") else dest_iata
    st.session_state["_last_currency"]  = currency_sel

# ── Render results if we have them (persists across reruns) ──────────────────

outbound_df = st.session_state.get("_outbound_df")
return_df   = st.session_state.get("_return_df")

if outbound_df is not None:
    st.divider()

    # ── Outbound ──────────────────────────────────────────────────────────────
    st.subheader(f"🛫 Outbound Flights  ·  {st.session_state.get('_outbound_label', '')}")

    if not outbound_df.empty:
        ma, mb, mc = st.columns(3)
        ma.metric("Flights found", len(outbound_df))
        mb.metric("Cheapest",      f"{currency_sel} {outbound_df['Price'].min()}")
        mc.metric("Average price", f"{currency_sel} {round(outbound_df['Price'].mean(), 2)}")
        st.divider()

    render_flight_cards(outbound_df, "outbound_flight")

    sel_out = st.session_state.get("selected_outbound_flight")
    if sel_out:
        st.success(f"✅ Outbound selected: **{sel_out.get('Flight Number')}**  ·  {sel_out.get('Departure')}")

    st.divider()

    # ── Return ────────────────────────────────────────────────────────────────
    st.subheader(f"🛬 Return Flights  ·  {st.session_state.get('_return_label', '')}")

    if not return_df.empty:
        ra, rb, rc = st.columns(3)
        ra.metric("Flights found", len(return_df))
        rb.metric("Cheapest",      f"{currency_sel} {return_df['Price'].min()}")
        rc.metric("Average price", f"{currency_sel} {round(return_df['Price'].mean(), 2)}")
        st.divider()

    render_flight_cards(return_df, "return_flight")

    sel_ret = st.session_state.get("selected_return_flight")
    if sel_ret:
        st.success(f"✅ Return selected: **{sel_ret.get('Flight Number')}**  ·  {sel_ret.get('Departure')}")

# ── Summary & proceed — always rendered so it persists ───────────────────────

sel_out = st.session_state.get("selected_outbound_flight")
sel_ret = st.session_state.get("selected_return_flight")

if sel_out or sel_ret:
    st.divider()
    st.subheader("🧾 Your Selected Flights")

    s1, s2 = st.columns(2)

    with s1:
        if sel_out:
            st.markdown("**🛫 Outbound**")
            st.write(f"Route: {sel_out.get('Starting Airport')} → {sel_out.get('Destination Airport')}")
            st.write(f"Departure: {sel_out.get('Departure')}")
            st.write(f"Flight: {sel_out.get('Flight Number')}  ·  {sel_out.get('Airline')}")
            st.write(f"Price: {sel_out.get('_currency')} {sel_out.get('Price')}")
            if st.button("❌ Clear outbound", key="clear_outbound"):
                del st.session_state["selected_outbound_flight"]
                st.rerun()
        else:
            st.info("No outbound flight selected yet.")

    with s2:
        if sel_ret:
            st.markdown("**🛬 Return**")
            st.write(f"Route: {sel_ret.get('Starting Airport')} → {sel_ret.get('Destination Airport')}")
            st.write(f"Departure: {sel_ret.get('Departure')}")
            st.write(f"Flight: {sel_ret.get('Flight Number')}  ·  {sel_ret.get('Airline')}")
            st.write(f"Price: {sel_ret.get('_currency')} {sel_ret.get('Price')}")
            if st.button("❌ Clear return", key="clear_return"):
                del st.session_state["selected_return_flight"]
                st.rerun()
        else:
            st.info("No return flight selected yet.")

    if sel_out and sel_ret:
        curr      = sel_out.get("_currency", st.session_state.get("_last_currency", "GBP"))
        total     = (sel_out.get("Price") or 0) + (sel_ret.get("Price") or 0)

        st.session_state["selected_flights"] = {
            "outbound":         sel_out,
            "return":           sel_ret,
            "currency":         curr,
            "total_price":      total,
            "destination_iata": st.session_state.get("_last_dest_iata", ""),
            "destination_city": st.session_state.get("_last_dest_city", ""),
        }

        st.success(f"✅ Total estimated flight cost: **{curr} {total}**")

        if st.button("📋 Go to trip review →", type="primary"):
            st.switch_page("pages/4_trip_review.py")
    else:
        st.caption("Select both an outbound and return flight to see your total cost and continue.")
