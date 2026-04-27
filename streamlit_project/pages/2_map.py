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

# ── Date header (above title) ─────────────────────────────────────────────────

start, end, nights = render_date_header()

# ── Page title ────────────────────────────────────────────────────────────────

st.title("🏨 Find Hotels & Activities")
st.caption("Search for hotels, nightclubs, and activities at your chosen destination.")

# ── Helper functions ──────────────────────────────────────────────────────────

def search_places(location, category):
    url = "https://places.googleapis.com/v1/places:searchText"
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key is None:
        st.error("GOOGLE_API_KEY is not set. Please add it to your environment variables.")
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
    data = response.json()

    places = []
    for place in data.get("places", []):
        places.append({
            "name":        place["displayName"]["text"],
            "address":     place.get("formattedAddress", "Unknown"),
            "rating":      place.get("rating", 0),
            "reviews":     place.get("userRatingCount", 0),
            "price_level": place.get("priceLevel", -1),
            "lat":         place.get("location", {}).get("latitude", 0),
            "lng":         place.get("location", {}).get("longitude", 0),
            "website":     place.get("websiteUri", None),
        })
    return places


def filter_places(places, min_rating=0, max_price=4):
    return [p for p in places if p["rating"] >= min_rating and p["price_level"] <= max_price]


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

# ── Search form — city pre-filled from session state ──────────────────────────

st.subheader("🔍 Search")

# Pull city chosen on previous page (if any)
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
    min_rating = st.slider("Minimum rating ⭐", 0.0, 5.0, 4.0, step=0.5)
    max_price  = st.selectbox(
        "Max price level 💰",
        options=[0, 1, 2, 3, 4],
        index=2,
        format_func=lambda x: ["Free", "Inexpensive", "Moderate", "Expensive", "Very expensive"][x],
    )

# Auto-search if arriving from destination page with a city already selected
auto_search = saved_city != "" and st.session_state.get("_map_auto_searched") != saved_city

search_clicked = st.button("Search", type="primary")

# ── Results ───────────────────────────────────────────────────────────────────

if search_clicked or auto_search:
    if not location.strip():
        st.error("Please enter a destination before searching.")
    else:
        if auto_search:
            st.session_state["_map_auto_searched"] = saved_city

        with st.spinner(f"Searching for {category.lower()} in {location}…"):
            places   = search_places(location.strip(), category)
            filtered = filter_places(places, min_rating, max_price)

        st.markdown(f"**{len(filtered)} result{'s' if len(filtered) != 1 else ''} found** in {location}")

        if filtered:
            plot_map(filtered)
            st.divider()

            price_labels = {-1: "Unknown", 0: "Free", 1: "Inexpensive", 2: "Moderate", 3: "Expensive", 4: "Very expensive"}

            # Check if a hotel is already selected
            currently_selected = st.session_state.get("selected_hotel", {}).get("name", None)
            if currently_selected:
                st.success(f"✅ Currently selected: **{currently_selected}** — scroll down to change or confirm your choice.")

            for p in filtered:
                with st.container():
                    r_col1, r_col2, r_col3 = st.columns([3, 1, 1])

                    with r_col1:
                        is_selected = currently_selected == p["name"]
                        header = f"{'✅ ' if is_selected else ''}{p['name']}"
                        st.subheader(header)
                        st.write(f"📍 {p['address']}")
                        st.write(f"⭐ {p['rating']} ({p['reviews']} reviews)  ·  💰 {price_labels.get(p['price_level'], 'Unknown')}")

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
                                "price_level": price_labels.get(p["price_level"], "Unknown"),
                                "website":     p["website"],
                                "city":        location.strip(),
                            }
                            st.rerun()

                    st.divider()
        else:
            st.info("No results matched your filters. Try lowering the minimum rating or raising the max price level.")

# ── Confirm & next step ───────────────────────────────────────────────────────

selected_hotel = st.session_state.get("selected_hotel", None)

if selected_hotel:
    st.divider()
    st.success(f"✅ Hotel selected: **{selected_hotel['name']}**, {selected_hotel['city']}")
    if st.button("📋 Review your trip →", type="primary"):
        st.switch_page("pages/3_trip_review.py")
elif saved_city:
    st.divider()
    st.caption("Select a hotel above to continue to your trip review.")
