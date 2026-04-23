import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="🌴 Holiday Planner", layout="wide")

# --- City database with tags ---
CITIES = {
    # Indonesia
    "Bali":      {
        "lat": -8.3405,  "lon": 115.0920, "country": "Indonesia", "flag": "🇮🇩",
        "tags": {"beach", "nightlife", "culture", "nature", "budget-friendly", "surf"},
    },
    "Jakarta":   {
        "lat": -6.2088,  "lon": 106.8456, "country": "Indonesia", "flag": "🇮🇩",
        "tags": {"city", "culture", "nightlife", "budget-friendly"},
    },
    "Lombok":    {
        "lat": -8.6500,  "lon": 116.3242, "country": "Indonesia", "flag": "🇮🇩",
        "tags": {"beach", "nature", "surf", "budget-friendly", "quiet"},
    },
    # Brazil
    "Rio de Janeiro": {
        "lat": -22.9068, "lon": -43.1729, "country": "Brazil", "flag": "🇧🇷",
        "tags": {"beach", "nightlife", "culture", "city", "surf"},
    },
    "Florianópolis":  {
        "lat": -27.5954, "lon": -48.5480, "country": "Brazil", "flag": "🇧🇷",
        "tags": {"beach", "surf", "nature", "quiet"},
    },
    "Salvador":       {
        "lat": -12.9714, "lon": -38.5014, "country": "Brazil", "flag": "🇧🇷",
        "tags": {"beach", "culture", "nightlife", "budget-friendly"},
    },
    # Spain
    "Barcelona":  {
        "lat": 41.3851, "lon":  2.1734, "country": "Spain", "flag": "🇪🇸",
        "tags": {"beach", "nightlife", "culture", "city", "food"},
    },
    "Seville":    {
        "lat": 37.3891, "lon": -5.9845, "country": "Spain", "flag": "🇪🇸",
        "tags": {"culture", "city", "food", "quiet"},
    },
    "Mallorca":   {
        "lat": 39.6953, "lon":  2.9113, "country": "Spain", "flag": "🇪🇸",
        "tags": {"beach", "nature", "quiet", "luxury"},
    },
    # Existing
    "Bangkok":    {
        "lat": 13.7563, "lon": 100.5018, "country": "Thailand",  "flag": "🇹🇭",
        "tags": {"city", "culture", "nightlife", "food", "budget-friendly"},
    },
    "Cartagena":  {
        "lat": 10.3910, "lon": -75.4794, "country": "Colombia",  "flag": "🇨🇴",
        "tags": {"beach", "culture", "city", "budget-friendly"},
    },
    "Tenerife":   {
        "lat": 28.2916, "lon": -16.6291, "country": "Spain",     "flag": "🇪🇸",
        "tags": {"beach", "nature", "quiet", "surf"},
    },
    "Phuket":     {
        "lat":  7.9519, "lon":  98.3381, "country": "Thailand",  "flag": "🇹🇭",
        "tags": {"beach", "nightlife", "culture", "budget-friendly", "surf"},
    },
    "Maldives":   {
        "lat":  3.2028, "lon":  73.2207, "country": "Maldives",  "flag": "🇲🇻",
        "tags": {"beach", "luxury", "quiet", "nature"},
    },
    "Lisbon":     {
        "lat": 38.7223, "lon":  -9.1393, "country": "Portugal",  "flag": "🇵🇹",
        "tags": {"city", "culture", "food", "nightlife", "quiet"},
    },
    "Zanzibar":   {
        "lat": -6.1659, "lon":  39.2026, "country": "Tanzania",  "flag": "🇹🇿",
        "tags": {"beach", "culture", "nature", "quiet", "budget-friendly"},
    },
}

# Human-readable tag labels with icons
TAG_META = {
    "beach":          {"label": "Beach",          "icon": "🏖️"},
    "city":           {"label": "City Break",     "icon": "🏙️"},
    "nightlife":      {"label": "Nightlife",       "icon": "🎉"},
    "culture":        {"label": "Culture",         "icon": "🏛️"},
    "nature":         {"label": "Nature",          "icon": "🌿"},
    "food":           {"label": "Food Scene",      "icon": "🍜"},
    "surf":           {"label": "Surf",            "icon": "🏄"},
    "quiet":          {"label": "Quiet / Relaxed", "icon": "🧘"},
    "luxury":         {"label": "Luxury",          "icon": "💎"},
    "budget-friendly":{"label": "Budget Friendly", "icon": "💸"},
}

WMO_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "🌤️"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Icy fog", "🌫️"),
    51: ("Light drizzle", "🌧️"), 53: ("Drizzle", "🌧️"), 55: ("Heavy drizzle", "🌧️"),
    61: ("Light rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "❄️"), 73: ("Snow", "❄️"), 75: ("Heavy snow", "❄️"),
    80: ("Showers", "🌦️"), 81: ("Heavy showers", "🌦️"), 82: ("Violent showers", "🌦️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm + hail", "⛈️"), 99: ("Severe storm", "⛈️"),
}

def wmo_label(code):
    desc, emoji = WMO_CODES.get(code, (f"Code {code}", "🌡️"))
    return f"{emoji} {desc}"

@st.cache_data(show_spinner=False)
def get_forecast(lat, lon, start_date, end_date):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        f"precipitation_sum,precipitation_probability_max,weathercode"
        f"&timezone=auto"
        f"&start_date={start_date}&end_date={end_date}"
    )
    return requests.get(url).json().get("daily", {})

def score_city(stats, prefs):
    temp_mid = (prefs["temp_min"] + prefs["temp_max"]) / 2
    temp_diff = abs(stats["avg_temp"] - temp_mid)
    temp_range = (prefs["temp_max"] - prefs["temp_min"]) / 2 + 5
    temp_score = max(0, 1 - temp_diff / temp_range)

    rain_score = max(0, 1 - stats["avg_rain_prob"] / 100)

    nights = stats["total_days"]
    sun_score = max(0, 1 - stats["rainy_days"] / max(nights, 1))

    w_temp = prefs["w_temp"] / 100
    w_rain = prefs["w_rain"] / 100
    w_sun  = prefs["w_sun"]  / 100

    score = (temp_score * w_temp + rain_score * w_rain + sun_score * w_sun) * 100
    return round(score, 1)

def cities_matching_tags(required_tags, excluded_tags):
    """Return city names that match tag filters."""
    matched = []
    for city, info in CITIES.items():
        city_tags = info["tags"]
        if required_tags and not required_tags.issubset(city_tags):
            continue
        if excluded_tags and excluded_tags.intersection(city_tags):
            continue
        matched.append(city)
    return matched

# ─── UI ───────────────────────────────────────────────────────────────────────

st.title("🌴 Holiday Planner")
st.caption("Compare destinations for your travel window and rank them by your preferences.")

with st.sidebar:
    # ── TAG FILTER SECTION ──────────────────────────────────────────────────
    st.header("🏷️ Filter by Vibe")
    st.caption("Select tags to narrow down cities automatically.")

    all_tags = sorted(TAG_META.keys())

    must_have_labels = st.multiselect(
        "Must have",
        options=all_tags,
        format_func=lambda t: f"{TAG_META[t]['icon']} {TAG_META[t]['label']}",
        placeholder="e.g. Beach, Nightlife...",
        key="must_have",
    )
    exclude_labels = st.multiselect(
        "Exclude",
        options=[t for t in all_tags if t not in must_have_labels],
        format_func=lambda t: f"{TAG_META[t]['icon']} {TAG_META[t]['label']}",
        placeholder="e.g. City Break, Luxury...",
        key="exclude",
    )

    required_tags = set(must_have_labels)
    excluded_tags = set(exclude_labels)

    # Compute tag-filtered city list
    tag_filtered_cities = cities_matching_tags(required_tags, excluded_tags)

    if required_tags or excluded_tags:
        match_count = len(tag_filtered_cities)
        if match_count == 0:
            st.warning("No cities match these filters.")
        else:
            st.success(f"{match_count} cities match your filters.")

    st.divider()

    # ── MANUAL SELECTION ────────────────────────────────────────────────────
    st.header("🗺️ Destinations")

    # Default selection: use tag-filtered list if filters are active, else preset
    if required_tags or excluded_tags:
        default_selection = tag_filtered_cities
    else:
        default_selection = ["Bali", "Barcelona", "Rio de Janeiro", "Bangkok", "Tenerife", "Maldives"]

    selected_cities = st.multiselect(
        "Cities to compare",
        options=list(CITIES.keys()),
        default=default_selection,
        help="Auto-populated from tag filters above. You can add or remove cities manually.",
    )

    # Show tags for selected cities as a quick reference
    if selected_cities:
        with st.expander("🔍 View city tags", expanded=False):
            for city in selected_cities:
                tags = CITIES[city]["tags"]
                tag_pills = "  ".join(
                    f"{TAG_META[t]['icon']} {TAG_META[t]['label']}"
                    for t in sorted(tags)
                    if t in TAG_META
                )
                st.caption(f"**{city}**: {tag_pills}")

    st.divider()

    # ── PREFERENCES ─────────────────────────────────────────────────────────
    st.header("⚙️ Your Preferences")
    st.caption("Adjust to match what matters most to you.")

    temp_range = st.slider(
        "Ideal temperature range (°C)",
        min_value=10, max_value=45,
        value=(24, 32)
    )

    st.markdown("**What matters most?**")
    w_temp = st.slider("🌡️ Temperature match", 0, 100, 40)
    w_rain = st.slider("🌧️ Low rain probability", 0, 100, 35)
    w_sun  = st.slider("☀️ Sunny days", 0, 100, 25)

    total_w = w_temp + w_rain + w_sun
    if total_w == 0:
        st.error("Weights can't all be zero.")
        st.stop()

    w_temp_n = round(w_temp / total_w * 100)
    w_rain_n = round(w_rain / total_w * 100)
    w_sun_n  = round(w_sun  / total_w * 100)
    st.caption(f"Normalised: 🌡️ {w_temp_n}% · 🌧️ {w_rain_n}% · ☀️ {w_sun_n}%")

    prefs = {
        "temp_min": temp_range[0], "temp_max": temp_range[1],
        "w_temp": w_temp_n, "w_rain": w_rain_n, "w_sun": w_sun_n,
    }

# --- Date inputs ---
st.subheader("📅 Travel Dates")
col1, col2 = st.columns(2)
today = date.today()
with col1:
    start = st.date_input("Departure", value=today + timedelta(days=7),
                           min_value=today, max_value=today + timedelta(days=13))
with col2:
    end = st.date_input("Return", value=today + timedelta(days=14),
                         min_value=today + timedelta(days=1), max_value=today + timedelta(days=14))

if start >= end:
    st.error("Return date must be after departure date.")
    st.stop()

nights = (end - start).days
st.info(f"📅 **{nights} nights** · {start.strftime('%d %b')} → {end.strftime('%d %b %Y')}")

if not selected_cities:
    st.warning("Select at least one city in the sidebar.")
    st.stop()

# Show active filters as pills above results
if required_tags or excluded_tags:
    filter_summary_parts = []
    if required_tags:
        filter_summary_parts.append(
            "✅ " + " · ".join(f"{TAG_META[t]['icon']} {TAG_META[t]['label']}" for t in sorted(required_tags))
        )
    if excluded_tags:
        filter_summary_parts.append(
            "🚫 " + " · ".join(f"{TAG_META[t]['icon']} {TAG_META[t]['label']}" for t in sorted(excluded_tags))
        )
    st.caption("Active filters: " + "  |  ".join(filter_summary_parts))

# --- Fetch forecasts ---
st.subheader("🏆 Ranked Destinations")

with st.spinner("Fetching forecasts..."):
    results = []
    for city in selected_cities:
        info = CITIES[city]
        daily = get_forecast(info["lat"], info["lon"], start.isoformat(), end.isoformat())
        if not daily or "temperature_2m_mean" not in daily:
            continue

        avg_temp      = round(sum(daily["temperature_2m_mean"]) / len(daily["temperature_2m_mean"]), 1)
        max_temp      = round(max(daily["temperature_2m_max"]), 1)
        min_temp      = round(min(daily["temperature_2m_min"]), 1)
        total_rain    = round(sum(daily["precipitation_sum"]), 1)
        avg_rain_prob = round(sum(daily["precipitation_probability_max"]) / len(daily["precipitation_probability_max"]))
        rainy_days    = sum(1 for p in daily["precipitation_sum"] if p > 1.0)
        dominant_code = max(set(daily["weathercode"]), key=daily["weathercode"].count)

        stats = {
            "avg_temp": avg_temp, "max_temp": max_temp, "min_temp": min_temp,
            "total_rain": total_rain, "avg_rain_prob": avg_rain_prob,
            "rainy_days": rainy_days, "total_days": len(daily["time"]),
            "dominant_code": dominant_code,
        }

        results.append({
            "city": city, "info": info, "stats": stats, "daily": daily,
            "score": score_city(stats, prefs),
        })

results.sort(key=lambda x: x["score"], reverse=True)

medals = ["🥇", "🥈", "🥉"]

for rank, r in enumerate(results):
    city  = r["city"]
    info  = r["info"]
    s     = r["stats"]
    score = r["score"]
    medal = medals[rank] if rank < 3 else f"#{rank+1}"

    city_tags = info.get("tags", set())
    tag_display = "  ".join(
        f"{TAG_META[t]['icon']} {TAG_META[t]['label']}"
        for t in sorted(city_tags)
        if t in TAG_META
    )

    with st.expander(
        f"{medal} **{city}** {info['flag']} {info['country']}  —  "
        f"Score: **{score}/100**  ·  {wmo_label(s['dominant_code'])}  ·  "
        f"Avg {s['avg_temp']}°C  ·  {s['rainy_days']} rainy days",
        expanded=(rank == 0),
    ):
        # Tag pills row
        if tag_display:
            st.caption(f"**Vibes:** {tag_display}")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Avg Temp",    f"{s['avg_temp']}°C")
        c2.metric("High / Low",  f"{s['max_temp']}° / {s['min_temp']}°")
        c3.metric("Total Rain",  f"{s['total_rain']} mm")
        c4.metric("Rain Chance", f"{s['avg_rain_prob']}%")
        c5.metric("Rainy Days",  f"{s['rainy_days']} / {s['total_days']}")

        daily = r["daily"]
        day_rows = []
        for i, d in enumerate(daily["time"]):
            code = daily["weathercode"][i]
            day_rows.append({
                "Date": d,
                "Weather": wmo_label(code),
                "High °C": daily["temperature_2m_max"][i],
                "Low °C": daily["temperature_2m_min"][i],
                "Rain mm": daily["precipitation_sum"][i],
                "Rain %": daily["precipitation_probability_max"][i],
            })

        day_df = pd.DataFrame(day_rows).set_index("Date")
        st.dataframe(day_df, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("🌡️ Temperature (°C)")
            st.line_chart(pd.DataFrame({
                "High": daily["temperature_2m_max"],
                "Low":  daily["temperature_2m_min"],
            }, index=daily["time"]))
        with col_b:
            st.caption("🌧️ Rain (mm)")
            st.bar_chart(pd.DataFrame(
                {"Rain mm": daily["precipitation_sum"]},
                index=daily["time"]
            ))

# --- Summary comparison table ---
st.divider()
st.subheader("📊 Full Comparison Table")

table_rows = []
for rank, r in enumerate(results):
    s = r["stats"]
    city_tags = r["info"].get("tags", set())
    tag_str = " ".join(TAG_META[t]["icon"] for t in sorted(city_tags) if t in TAG_META)
    table_rows.append({
        "Rank":       f"{medals[rank] if rank < 3 else rank+1}",
        "City":       f"{r['info']['flag']} {r['city']}",
        "Country":    r["info"]["country"],
        "Vibes":      tag_str,
        "Score /100": r["score"],
        "Condition":  wmo_label(s["dominant_code"]),
        "Avg °C":     s["avg_temp"],
        "Max °C":     s["max_temp"],
        "Min °C":     s["min_temp"],
        "Rain mm":    s["total_rain"],
        "Rain %":     s["avg_rain_prob"],
        "Rainy Days": s["rainy_days"],
    })

st.dataframe(pd.DataFrame(table_rows).set_index("Rank"), use_container_width=True)
