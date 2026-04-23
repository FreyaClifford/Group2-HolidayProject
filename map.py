import requests
def search_places(location, page):
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.location"
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
            "lat": place["location"]["latitude"],
            "lng": place["location"]["longitude"]
        })

    return places


import pydeck as pdk

def filter(places, min_rating=0, max_price=4):
    filtered = []

    for h in places:
        if h["rating"] >= min_rating:
        #and h["price_level"] <= max_price:
            filtered.append(h)

    #df = pd.DataFrame(filtered)
    #return df
    return filtered

def plot_hotels(filtered):
    df = pd.DataFrame(filtered)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lng, lat]',
        get_radius=120,
        get_fill_color='[255, 0, 200, 160]',
        #  if page == "Nightclubs" else '[0, 128, 255, 160]',
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
        #map_style="mapbox://styles/mapbox/navigation-night-v1" if page == "Nightclubs" else "mapbox://styles/mapbox/streets-v11"
    ))

import streamlit as st
import pandas as pd
 
st.title("Hotel and Ammentities Finder")

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
        st.subheader(p["name"])
        st.write(f"📍 {p['address']}")
        st.write(f"⭐ {p['rating']}")

