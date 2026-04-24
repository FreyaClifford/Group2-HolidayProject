import requests
import os


def search_places(location, page):
    url = "https://places.googleapis.com/v1/places:searchText"

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key is None:
        st.write("GOOGLE_API_KEY not set")
        exit

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.location,places.websiteUri"
    }

    data = {
        "textQuery": f"{page} in {location}"
    }

    response = requests.post(url, headers=headers, json=data)
    data = response.json()

    places = []

    for place in data.get("places", []):
        places.append({
            "name": place['displayName']['text'],
            "address": place.get("formattedAddress","unknown"),
            "rating": place.get("rating", 0),
            "reviews": place.get("userRatingCount", 0),
            "price_level": place.get("priceLevel", -1),
            "lat": place.get("location", {}).get("latitude", 0),
            "lng": place.get("location", {}).get("longitude", 0),
            "website":place.get("websiteUri",None)
        })

    return places

def filter(places, min_rating=0, max_price=4):
    filtered = []

    for h in places:
        if h["rating"] >= min_rating and h["price_level"] <= max_price:
            filtered.append(h)
    return filtered

import pydeck as pdk


def plot_hotels(filtered):

    #If there are no places after fitering dont create a map 
    if not filtered:
        st.warning("No locations to display")
        return

    df = pd.DataFrame(filtered)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lng, lat]',
        get_radius=120,
        get_fill_color='[255, 0, 200, 160]',
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

import streamlit as st
import pandas as pd
 
st.title("Hotel and Amenities Finder")

# User inputs
location = st.text_input("Enter location", "London")
page = st.selectbox(
    "What are you looking for?",
    ["Hotels", "Nightclubs", "Activities"]
)
min_rating = st.slider("Minimum rating", 0.0, 5.0, 4.0)
max_price = st.selectbox("Max price level", [0,1,2,3,4], index=2)

if st.button("Search"):
    places = search_places(location, page)
    filtered = filter(places, min_rating, max_price)
    plot_hotels(filtered)

    st.write(f"Found {len(filtered)} results")

    for p in filtered:
        with st.container():
            st.subheader(p["name"])
            st.write(f"📍 {p['address']}")
            st.write(f"⭐ {p['rating']} ({p['reviews']} reviews)")
            st.write(f"💰 Price level: {p['price_level']}")

            if p["website"]:
                st.markdown(f"[🌐 Visit website]({p['website']})")

            st.divider()


