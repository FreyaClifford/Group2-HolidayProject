import requests
import os
import streamlit as st
import json
import pandas as pd
from datetime import datetime
import time

# Page formatting
st.set_page_config(page_title="Cheap Live Flight Tickets", page_icon="✈️", layout="wide")

st.title("✈️ Cheap Live Flight Tickets")
st.caption("Search for low-cost flights for your chosen destination.")

# Functions for: Getting codes from names (inputted by user) AND getting names of the codes (outputted from API response)
TOKEN = "09e2f28e8bb7c3afdd252db783410cae"

BASE_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

name_cache = {}

airline_cache = None

def get_airline_lookup():
    global airline_cache

    if airline_cache is not None:
        return airline_cache

    url = "http://api.travelpayouts.com/data/en/airlines.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    airlines = response.json()

    airline_cache = {}
    for item in airlines:
        code = str(item.get("code", "")).strip().upper()
        name = item.get("name")

        if code:
            airline_cache[code] = name or code

    return airline_cache

def resolve_destination(user_input, token):
    query = user_input.strip()

    if len(query) in [2, 3] and query.replace(" ", "").isalpha():
        return query.upper()

    autocomplete_url = "https://autocomplete.travelpayouts.com/places2"

    params = {
        "term": query,
        "locale": "en",
        "types[]": ["country", "city", "airport"]
    }

    response = requests.get(autocomplete_url, params=params, timeout=30)
    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    best_match = results[0]
    place_type = str(best_match.get("type", "")).lower()

    if place_type == "country":
        return best_match.get("code")

    elif place_type == "city":
        return best_match.get("code")

    elif place_type == "airport":
        return best_match.get("code")

    return None

def get_place_name_from_code(code):
    query = str(code).strip().upper()

    if query in name_cache:
        return name_cache[query]

    autocomplete_url = "https://autocomplete.travelpayouts.com/places2"

    params = {
        "term": query,
        "locale": "en",
        "types[]": ["country", "city", "airport"]
    }

    response = requests.get(autocomplete_url, params=params, timeout=30)
    response.raise_for_status()

    results = response.json()

    if not results:
        name_cache[query] = query
        return query

    best_match = results[0]
    place_type = str(best_match.get("type", "")).lower()

    if place_type == "country":
        resolved_name = best_match.get("name") or query
    elif place_type == "city":
        resolved_name = best_match.get("name") or query
    elif place_type == "airport":
        resolved_name = best_match.get("name") or query
    else:
        resolved_name = best_match.get("name") or query

    name_cache[query] = resolved_name
    return resolved_name

# User Input
st.markdown("### Search Criteria")

col1, col2 = st.columns(2)

with col1:
    origin_choice = st.selectbox("Starting airport/city",[
        ("LON", "London"),
        ("MAN", "Manchester"),
        ("BHX", "Birmingham"),
        ("EDI", "Edinburgh"),
        ("GLA", "Glasgow"),
        ("BRS", "Bristol")
        ],
        format_func=lambda x: f"{x[1]} ({x[0]})"
    )
    dest = st.text_input("Desired destination", placeholder="Enter a city, airport, or country - e.g. Brazil, BR")
    depart = st.text_input("Planned departure date", placeholder="YYYY-MM or YYYY-MM-DD")

with col2:
    direct_bool = st.radio("Do you want direct flights only?", ["Yes", "No"], horizontal=True)
    currency_choice = st.selectbox("Currency", ["GBP", "USD", "EUR", "IDR", "BRL", "THB", "JPY", "AUD", "CAD", "SGD"], index = 0)
    trip_type = st.radio("Trip type", ["One-way", "Return"], horizontal=True)

return_date = ""
if trip_type == "Return":
    return_date = st.text_input("Planned return date", placeholder="YYYY-MM or YYYY-MM-DD")

direct_choice = "true" if direct_bool == "Yes" else "false"
one_way_choice = "true" if trip_type == "One-way" else "false"

search_clicked = st.button("Search")

# Requesting from api
if search_clicked:
    if not dest.strip() or not depart.strip():
        st.error("Please fill in destination and departure date before searching.")
        st.stop
    
    if trip_type == "Return" and not return_date.strip():
        st.error("Please fill in a return date for a return journey.")
        st.stop()
        
    resolved_dest = resolve_destination(dest, TOKEN)

    if not resolved_dest:
        st.error("Could not resolve that destination. Try a country, city, airport, or code.")
        st.stop()

    st.info(f"Using destination code: {resolved_dest}")

    params = {
        "origin": f"{origin_choice[0]}",
        "destination": resolved_dest,
        "departure_at": f"{depart.strip()}",
        "one_way": one_way_choice,
        "one_way": "true",
        "direct": direct_choice,
        "sorting": "price",
        "currency": f"{currency_choice.strip().upper()}",
        "limit": 10,
        "page": 1,
        "token": TOKEN
    }

    if trip_type == "Return":
            params["return_at"] = return_date.strip()

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        st.error("The API returned an empty response.")
        st.stop()

    data = response.json()

# Showing response
    rows = []
    for item in data.get("data", []):

        raw_departure = item.get("departure_at")
        if raw_departure:
            formatted_departure = datetime.fromisoformat(raw_departure).strftime("%d %b %Y - %H:%M")
        else:
            formatted_departure = "Unknown"
        
        raw_return = item.get("return_at")
        if raw_return:
            formatted_return = datetime.fromisoformat(raw_return).strftime("%d %b %Y - %H:%M")
        else:
            formatted_return = "Not applicable"
        
        destination_name = get_place_name_from_code(item.get("destination"))
        starting_airport_name = get_place_name_from_code(item.get("origin_airport"))
        destination_airport_name = get_place_name_from_code(item.get("destination_airport"))
        
        airline_lookup = get_airline_lookup()
        airline_code = str(item.get("airline") or "").strip().upper()
        airline_name = airline_lookup.get(airline_code, airline_code)

        rows.append({
            "Starting Place": item.get("origin"),
            "Destination code": item.get("destination"),
            "Destination name": destination_name,
            "Starting Airport code": item.get("origin_airport"),
            "Starting Airport name": starting_airport_name,
            "Destination Airport code": item.get("destination_airport"),
            "Destination Airport name": destination_airport_name,
            "Price": item.get("price"),
            "Airline code": item.get("airline"),
            "Airline name": airline_name,
            "Departure Time": formatted_departure,
            "Return Time": formatted_return,
            "No. of Transfers": item.get("transfers"),
            "Flight Number": item.get("flight_number"),
            "Approximate Duration (hours)": int(round((item.get("duration_to") or 0) / 60)),
            "Link": "https://www.aviasales.com" + str(item.get("link") or "")
        })

    df = pd.DataFrame(rows)

    st.subheader("Recommended Flight Options")
    st.markdown("---")

    for _, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### {row['Destination name']}")
                st.caption(f"With **{row['Airline name']}**")
                st.write(f"**Route:** {row['Starting Airport name']} ({row['Starting Airport code']}) → {row['Destination Airport name']} ({row['Destination Airport code']})")
                st.write(f"**Departure:** {row['Departure Time']}")
                st.write(f"**Flight Number:** {row['Flight Number']}")
                
            with col2:
                st.metric("", f"{currency_choice.strip().upper()} {row['Price']}")
                st.write(f"**Transfers:** {row['No. of Transfers']}")
                st.write(f"**Duration:** ~{row['Approximate Duration (hours)']} hrs")
                st.write(f"**Return:** {row['Return Time']}")

            with col3:
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.markdown(f"[See current ticket options]({row['Link']})")

            st.markdown("---")

    if not df.empty:
        st.subheader("Results Overview")

        colA, colB = st.columns(2)
        colA.metric("Flights Found", len(df))
        colB.metric("Average Price", f"{currency_choice.strip().upper()} {round(df['Price'].mean(), 2)}")

    else:
        st.warning("No flight data found for that search.")
