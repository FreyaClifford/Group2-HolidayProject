import requests
import os
from dotenv import load_dotenv
import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime 
import time

st.title("Cheap Live Flight Tickets")

from pathlib import Path

csv_path = Path(__file__).parent / ".." / "Data" / "iata_codes_clean.csv"
codes_df = pd.read_csv(csv_path.resolve(), encoding="latin-1")
#codes_df = pd.read_csv("iata_codes_clean.csv", encoding = "latin-1")

load_dotenv()
TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

BASE_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

dest = st.text_input("What is your desired destination? (IATA code of a city/ airport)")
depart = st.text_input("What is your planned departure date? (yyyy-mm OR yyyy-mm-dd)")
direct_bool = st.radio("Do you want direct flights only?", ["Yes", "No"])
currency_choice = st.text_input("What is you preferred currency choice? (ISO-4217 code)")

direct_choice = "true" if direct_bool == "Yes" else "false"

search_clicked = st.button("Search")

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
        data = response.json()

        rows = []
        for item in data.get("data", []):
            match = codes_df[codes_df["iata_code"] == item.get("destination")]
            destination_country = match["country_name"].iloc[0] if not match.empty else item.get("destination")
            
            rows.append({
                "Starting Place": item.get("origin"),
                "Destination": destination_country,
                "Starting Airport": item.get("origin_airport"),
                "Destination Airport": item.get("destination_airport"),
                "Price": item.get("price"),
                "Airline": item.get("airline"),
                "Departure Time": item.get("departure_at"),
                "No. of Transfers": item.get("transfers"),
                "Flight Number": item.get("flight_number"),
                "Approximate duration (hours)": int(round(item.get("duration_to") / 60)),
                "Link": "https://www.aviasales.com" + item.get("link")
            })

        df = pd.DataFrame(rows)

        if not df.empty:
                st.write("Flight results:")
                st.dataframe(df)
        else:
            st.warning("No flight data found for that search.")