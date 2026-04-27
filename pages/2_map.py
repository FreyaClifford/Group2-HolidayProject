import requests
import os
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import date, timedelta
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_dates import render_date_header

st.set_page_config(page_title="🏨 Find Hotels & Activities", page_icon="🏨", layout="wide")

st.session_state["current_step"] = 2

# ── Date header ───────────────────────────────────────────────────────────────

start, end, nights = render_date_header()

# ── Page title ────────────────────────────────────────────────────────────────

st.title("🏨 Find Hotels & Activities")
st.caption("Search for hotels, nightclubs, and activities at your chosen destination.")

# ── Price level helpers ───────────────────────────────────────────────────────

PRICE_LABELS      = {-1: "Unknown", 0: "Free", 1: "Inexpensive", 2: "Moderate", 3: "Expensive", 4: "Very expensive"}
PRICE_LEVEL_NAMES = ["Free", "Inexpensive", "Moderate", "Expensive", "Very expensive"]

PRICE_STR_TO_INT = {
    "PRICE_LEVEL_FREE":            0,
    "PRICE_LEVEL_INEXPENSIVE":     1,
    "PRICE_LEVEL_MODERATE":        2,
    "PRICE_LEVEL_EXPENSIVE":       3,
    "PRICE_LEVEL_VERY_EXPENSIVE":  4,
}

def normalise_price(raw):
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        return PRICE_STR_TO_INT.get(raw, -1)
    return -1

# ── API + filter helpers ──────────────────────────────────────────────────────

def search_places(location, category):
    url = "https://places.googleapis.com/v1/places:searchText"
    try:
        api_key = st.secrets["google"]["GOOGLE_API_KEY"]
    except KeyError:
        st.error("GOOGLE_API_KEY not found. Add it to .streamlit/secrets.toml")
        st.stop()

    if not api_key:
        st.error("GOOGLE_API_KEY is not set.")
        st.stop()

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,places.rating,"
            "places.userRatingCount,places.priceLevel,places.location,places.websiteUri"
        ),
    }

    response = requests.post(url, headers=headers, json={"textQuery": f"{category} in {location}"})

    if response.status_code != 200:
        st.error(f"API error: {response.text}")
        return []

    places = []
    for place in response.json().get("places", []):
        places.append({
            "name":        place["displayName"]["text"],
            "address":     place.get("formattedAddress", "Unknown"),
            "rating":      place.get("rating", 0),
            "reviews":     place.get("userRatingCount", 0),
            "price_level": normalise_price(place.get("priceLevel", -1)),
            "lat":         place.get("location", {}).get("latitude", 0),
            "lng":         place.get("location", {}).get("longitude", 0),
            "website":     place.get("websiteUri", None),
        })
    return places


def filter_places(places, min_rating, max_rating, min_price, max_price):
    results = []
    for p in places:
        if p["rating"] < min_rating or p["rating"] > max_rating:
            continue
        price = p["price_level"]
        if price != -1 and (price < min_price or price > max_price):
            continue
        results.append(p)
    return results


def plot_map(filtered):
    if not filtered:
        st.warning("No locations to display on the map.")
        return
    df = pd.DataFrame(filtered)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lng, lat]",
        get_radius=120,
        get_fill_color="[255, 0, 200, 160]",
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lng"].mean(),
        zoom=12,
    )
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\n⭐ {rating}"},
    ))

# ── Search form ───────────────────────────────────────────────────────────────

st.subheader("🔍 Search")

saved_city = st.session_state.get("selected_city", "")

col1, col2 = st.columns(2)

with col1:
    location = st.text_input(
        "Destination",
        value=saved_city,
        placeholder="e.g. Bali, Barcelona, Bangkok",
    )
    category = st.selectbox("What are you looking for?", ["Hotels", "Nightclubs", "Activities"])

with col2:
    rating_range = st.slider(
        "Rating range ⭐",
        min_value=0.0,
        max_value=5.0,
        value=(3.5, 5.0),
        step=0.1,
        format="%.1f",
    )
    min_rating, max_rating = rating_range

    price_range = st.slider(
        "Price level 💰  (0 = Free → 4 = Very expensive)",
        min_value=0,
        max_value=4,
        value=(0, 4),
        step=1,
    )
    min_price, max_price = price_range
    st.caption(f"💰 **{PRICE_LEVEL_NAMES[min_price]}** → **{PRICE_LEVEL_NAMES[max_price]}**")

# Auto-search when arriving from destination page for the first time
auto_search = saved_city != "" and st.session_state.get("_map_auto_searched") != saved_city

search_clicked = st.button("🔍 Search", type="primary")

# ── Run search and cache results in session state ─────────────────────────────

if search_clicked or auto_search:
    if not location.strip():
        st.error("Please enter a destination before searching.")
    else:
        if auto_search:
            st.session_state["_map_auto_searched"] = saved_city

        with st.spinner(f"Searching for {category.lower()} in {location}…"):
            places = search_places(location.strip(), category)

        # Store raw places and search context so results survive reruns
        st.session_state["_map_places"]   = places
        st.session_state["_map_location"] = location.strip()
        st.session_state["_map_category"] = category

# ── Render results from session state (persists across reruns) ────────────────

cached_places   = st.session_state.get("_map_places")
cached_location = st.session_state.get("_map_location", "")
cached_category = st.session_state.get("_map_category", "")

if cached_places is not None:
    # Re-apply filters on every render so slider changes take effect immediately
    filtered = filter_places(cached_places, min_rating, max_rating, min_price, max_price)

    st.markdown(f"**{len(filtered)} result{'s' if len(filtered) != 1 else ''} found** in {cached_location}")

    if filtered:
        plot_map(filtered)
        st.divider()

        currently_selected = st.session_state.get("selected_hotel", {}).get("name")
        if currently_selected:
            st.success(f"✅ Currently selected: **{currently_selected}** — scroll down to change or confirm.")

        for p in filtered:
            with st.container():
                r_col1, r_col2, r_col3 = st.columns([3, 1, 1])

                with r_col1:
                    is_selected = currently_selected == p["name"]
                    st.subheader(f"{'✅ ' if is_selected else ''}{p['name']}")
                    st.write(f"📍 {p['address']}")
                    st.write(
                        f"⭐ {p['rating']} ({p['reviews']} reviews)  ·  "
                        f"💰 {PRICE_LABELS.get(p['price_level'], 'Unknown')}"
                    )

                with r_col2:
                    if p["website"]:
                        st.markdown(f"[🌐 Visit website]({p['website']})")

                with r_col3:
                    btn_label = "✅ Selected" if is_selected else "Select this hotel"
                    if st.button(btn_label, key=f"select_{p['name']}", disabled=is_selected):
                        st.session_state["selected_hotel"] = {
                            "name":        p["name"],
                            "address":     p["address"],
                            "rating":      p["rating"],
                            "reviews":     p["reviews"],
                            "price_level": PRICE_LABELS.get(p["price_level"], "Unknown"),
                            "website":     p["website"],
                            "city":        cached_location,
                        }
                        st.rerun()

                st.divider()
    else:
        st.info("No results matched your filters. Try widening the rating range or price level.")

# ── Confirm & next step — always rendered so selection persists ───────────────

st.divider()

selected_hotel = st.session_state.get("selected_hotel")

if selected_hotel:
    st.success(f"✅ Hotel selected: **{selected_hotel['name']}**, {selected_hotel['city']}")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write(f"📍 {selected_hotel['address']}")
        st.write(f"⭐ {selected_hotel['rating']}  ·  💰 {selected_hotel['price_level']}")
    with col_b:
        if st.button("❌ Clear selection", key="clear_hotel"):
            del st.session_state["selected_hotel"]
            st.rerun()
    if st.button("📋 Review your trip →", type="primary"):
        st.switch_page("pages/3_trip_review.py")
elif saved_city:
    st.caption("Select a hotel above to continue to your trip review.")
