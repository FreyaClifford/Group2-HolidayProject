import requests
import os
#from dotenv import load_dotenv
import streamlit as st
import json
import pandas as pd
#import matplotlib.pyplot as plt
from datetime import datetime 
import time

#Page formatting
st.set_page_config(page_title="Cheap Live Flight Tickets", page_icon="✈️", layout="wide")

st.title("✈️ Cheap Live Flight Tickets")
st.caption("Search for low-cost flights for your chosen destination.")

#from pathlib import Path

#csv_path = Path(__file__).parent / ".." / "Data" / "iata_codes_clean.csv"
#codes_df = pd.read_csv(csv_path.resolve(), encoding="latin-1")
#codes_df = pd.read_csv("iata_codes_clean.csv", encoding = "latin-1")

#User input
#load_dotenv()
#TRAVELPAYOUTS_TOKEN = "09e2f28e8bb7c3afdd252db783410cae"
TOKEN = "09e2f28e8bb7c3afdd252db783410cae"    #os.getenv("TRAVELPAYOUTS_TOKEN")

BASE_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

st.markdown("### Search Criteria")

col1, col2 = st.columns(2)

with col1:
    dest = st.text_input("Desired destination", placeholder = "IATA code of a city or airport, e.g. BKK")
    depart = st.text_input("Planned departure date", placeholder = "YYYY-MM or YYYY-MM-DD")

with col2:
    direct_bool = st.radio("Do you want direct flights only?", ["Yes", "No"], horizontal = True)
    currency_choice = st.text_input("Currency", placeholder = "ISO-4217 code, e.g. GBP")


direct_choice = "true" if direct_bool == "Yes" else "false"

search_clicked = st.button("Search")

#Requesting from api

if search_clicked:
    if not currency_choice.strip() or not dest.strip() or not depart.strip():
        st.error("Please fill in destination, departure date and currency choice before searching.")
    else:
        params = {
            "origin": "LON",
            "destination": f"{dest.strip().upper()}",
            "departure_at": f"{depart.strip()}",
            "one_way": "true",
            "direct": direct_choice,
            "sorting": "price",
            "currency": f"{currency_choice.strip().upper()}",
            "limit": 10,
            "page": 1,
            "token": TOKEN
            }

        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        if not response.text.strip():
            st.error("The API returned an empty response.")
            st.stop()
        
        data = response.json()

#Showing response 
        rows = []
        for item in data.get("data", []):
            #match = codes_df[codes_df["iata_code"] == item.get("destination")]
            #destination_country = match["country_name"].iloc[0] if not match.empty else item.get("destination")
            
            raw_departure = item.get("departure_at")
            if raw_departure:
                formatted_departure = datetime.fromisoformat(raw_departure).strftime("%d %b %Y - %H:%M")
            else:
                formatted_departure = "Unknown"

            rows.append({
                "Starting Place": item.get("origin"),
                "Destination": item.get("destination"),
                "Starting Airport": item.get("origin_airport"),
                "Destination Airport": item.get("destination_airport"),
                "Price": item.get("price"),
                "Airline": item.get("airline"),
                "Departure Time": item.get("departure_at"),
                "No. of Transfers": item.get("transfers"),
                "Flight Number": item.get("flight_number"),
                "Approximate Duration (hours)": int(round((item.get("duration_to") or 0) / 60)),
                "Link": "https://www.aviasales.com" + str(item.get("link") or "")
            })

        df = pd.DataFrame(rows)
        
        st.subheader("Flight Results")
        st.markdown("---")

        for _, row in df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"### {row['Destination']}")
                    st.caption(f"With **{row['Airline']}** airline")
                    st.write(f"**Route:** {row['Starting Airport']} → {row['Destination Airport']}")
                    st.write(f"**Departure:** {formatted_departure}")
                    st.write(f"**Flight Number:** {row['Flight Number']}")

                with col2:
                    st.metric("", f"{currency_choice.strip().upper()} {row['Price']}")
                    st.write(f"**Transfers:** {row['No. of Transfers']}")
                    st.write(f"**Duration:** ~{row['Approximate Duration (hours)']} hrs")

                with col3:
                    st.markdown(f"[Open Flight Link]({row['Link']})")

                st.markdown("---")

        if not df.empty:
                st.subheader("Results Overview")

                colA, colB= st.columns(2)
                colA.metric("Flights Found", len(df))
                colB.metric("Average Price", f"{currency_choice.strip().upper()} {round(df['Price'].mean(), 2)}")

                #st.subheader("Flight Results")
                #st.dataframe(df, use_container_width=True)
        else:
            st.warning("No flight data found for that search.")
