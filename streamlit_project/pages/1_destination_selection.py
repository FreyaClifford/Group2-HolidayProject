import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_dates import render_date_header

st.set_page_config(page_title="🌍 Pick a Destination", page_icon="🌍", layout="wide")

st.session_state["current_step"] = 1

# ── Date header (above title) ─────────────────────────────────────────────────

start, end, nights = render_date_header()

if nights == 0:
    st.stop()

# ── Page title ────────────────────────────────────────────────────────────────

st.title("🌍 Pick a Destination")
st.caption("Filter by vibe, tune your weather preferences, and see every destination ranked for your trip.")

# ── City database ─────────────────────────────────────────────────────────────

CITIES = {
    "Bali":           {"lat": -8.3405,  "lon": 115.0920, "country": "Indonesia", "flag": "🇮🇩", "tags": {"beach", "nightlife", "culture", "nature", "budget-friendly", "surf"}},
    "Jakarta":        {"lat": -6.2088,  "lon": 106.8456, "country": "Indonesia", "flag": "🇮🇩", "tags": {"city", "culture", "nightlife", "budget-friendly"}},
    "Lombok":         {"lat": -8.6500,  "lon": 116.3242, "country": "Indonesia", "flag": "🇮🇩", "tags": {"beach", "nature", "surf", "budget-friendly", "quiet"}},
    "Rio de Janeiro": {"lat": -22.9068, "lon": -43.1729, "country": "Brazil",    "flag": "🇧🇷", "tags": {"beach", "nightlife", "culture", "city", "surf"}},
    "Florianópolis":  {"lat": -27.5954, "lon": -48.5480, "country": "Brazil",    "flag": "🇧🇷", "tags": {"beach", "surf", "nature", "quiet"}},
    "Salvador":       {"lat": -12.9714, "lon": -38.5014, "country": "Brazil",    "flag": "🇧🇷", "tags": {"beach", "culture", "nightlife", "budget-friendly"}},
    "Barcelona":      {"lat": 41.3851,  "lon":  2.1734,  "country": "Spain",     "flag": "🇪🇸", "tags": {"beach", "nightlife", "culture", "city", "food"}},
    "Seville":        {"lat": 37.3891,  "lon": -5.9845,  "country": "Spain",     "flag": "🇪🇸", "tags": {"culture", "city", "food", "quiet"}},
    "Mallorca":       {"lat": 39.6953,  "lon":  2.9113,  "country": "Spain",     "flag": "🇪🇸", "tags": {"beach", "nature", "quiet", "luxury"}},
    "Bangkok":        {"lat": 13.7563,  "lon": 100.5018, "country": "Thailand",  "flag": "🇹🇭", "tags": {"city", "culture", "nightlife", "food", "budget-friendly"}},
    "Cartagena":      {"lat": 10.3910,  "lon": -75.4794, "country": "Colombia",  "flag": "🇨🇴", "tags": {"beach", "culture", "city", "budget-friendly"}},
    "Tenerife":       {"lat": 28.2916,  "lon": -16.6291, "country": "Spain",     "flag": "🇪🇸", "tags": {"beach", "nature", "quiet", "surf"}},
    "Phuket":         {"lat":  7.9519,  "lon":  98.3381, "country": "Thailand",  "flag": "🇹🇭", "tags": {"beach", "nightlife", "culture", "budget-friendly", "surf"}},
    "Maldives":       {"lat":  3.2028,  "lon":  73.2207, "country": "Maldives",  "flag": "🇲🇻", "tags": {"beach", "luxury", "quiet", "nature"}},
    "Lisbon":         {"lat": 38.7223,  "lon":  -9.1393, "country": "Portugal",  "flag": "🇵🇹", "tags": {"city", "culture", "food", "nightlife", "quiet"}},
    "Zanzibar":       {"lat": -6.1659,  "lon":  39.2026, "country": "Tanzania",  "flag": "🇹🇿", "tags": {"beach", "culture", "nature", "quiet", "budget-friendly"}},
}

TAG_META = {
    "beach":           {"label": "Beach",          "icon": "🏖️"},
    "city":            {"label": "City Break",     "icon": "🏙️"},
    "nightlife":       {"label": "Nightlife",       "icon": "🎉"},
    "culture":         {"label": "Culture",         "icon": "🏛️"},
    "nature":          {"label": "Nature",          "icon": "🌿"},
    "food":            {"label": "Food Scene",      "icon": "🍜"},
    "surf":            {"label": "Surf",            "icon": "🏄"},
    "quiet":           {"label": "Quiet / Relaxed", "icon": "🧘"},
    "luxury":          {"label": "Luxury",          "icon": "💎"},
    "budget-friendly": {"label": "Budget Friendly", "icon": "💸"},
}

WMO_CODES = {
    0: ("Clear sky", "☀️"),  1: ("Mainly clear", "🌤️"),  2: ("Partly cloudy", "🌤️"),
    3: ("Overcast", "☁️"),  45: ("Foggy", "🌫️"),         48: ("Icy fog", "🌫️"),
   51: ("Light drizzle", "🌧️"), 53: ("Drizzle", "🌧️"),  55: ("Heavy drizzle", "🌧️"),
   61: ("Light rain", "🌧️"),   63: ("Rain", "🌧️"),       65: ("Heavy rain", "🌧️"),
   71: ("Light snow", "❄️"),   73: ("Snow", "❄️"),        75: ("Heavy snow", "❄️"),
   80: ("Showers", "🌦️"),      81: ("Heavy showers", "🌦️"), 82: ("Violent showers", "🌦️"),
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
        f"&timezone=auto&start_date={start_date}&end_date={end_date}"
    )
    return requests.get(url).json().get("daily", {})

def score_city(stats, prefs):
    temp_mid   = (prefs["temp_min"] + prefs["temp_max"]) / 2
    temp_diff  = abs(stats["avg_temp"] - temp_mid)
    temp_range = (prefs["temp_max"] - prefs["temp_min"]) / 2 + 5
    temp_score = max(0, 1 - temp_diff / temp_range)
    rain_score = max(0, 1 - stats["avg_rain_prob"] / 100)
    sun_score  = max(0, 1 - stats["rainy_days"] / max(stats["total_days"], 1))
    return round(
        (temp_score * prefs["w_temp"] + rain_score * prefs["w_rain"] + sun_score * prefs["w_sun"]) / 100 * 100,
        1
    )

def cities_matching_tags(required_tags, excluded_tags):
    return [
        city for city, info in CITIES.items()
        if (not required_tags or required_tags.issubset(info["tags"]))
        and (not excluded_tags or not excluded_tags.intersection(info["tags"]))
    ]

# ── Step 1: Vibe filters ──────────────────────────────────────────────────────

with st.expander("🏷️ Step 1 — Filter by vibe", expanded=True):
    st.caption("Narrow the destination list by what matters to you.")
    all_tags = sorted(TAG_META.keys())
    fc1, fc2 = st.columns(2)
    with fc1:
        must_have_labels = st.multiselect(
            "Must have",
            options=all_tags,
            format_func=lambda t: f"{TAG_META[t]['icon']} {TAG_META[t]['label']}",
            placeholder="e.g. Beach, Nightlife…",
            key="must_have",
        )
    with fc2:
        exclude_labels = st.multiselect(
            "Exclude",
            options=[t for t in all_tags if t not in must_have_labels],
            format_func=lambda t: f"{TAG_META[t]['icon']} {TAG_META[t]['label']}",
            placeholder="e.g. City Break, Luxury…",
            key="exclude",
        )

    required_tags = set(must_have_labels)
    excluded_tags = set(exclude_labels)
    tag_filtered_cities = cities_matching_tags(required_tags, excluded_tags)

    if required_tags or excluded_tags:
        if not tag_filtered_cities:
            st.warning("No cities match these filters. Try adjusting your selections.")
        else:
            st.success(f"{len(tag_filtered_cities)} cities match your filters.")

# ── Step 2: Choose cities ─────────────────────────────────────────────────────

with st.expander("🗺️ Step 2 — Choose cities to compare", expanded=True):
    st.caption("Your vibe filters above update this list automatically. You can also add or remove cities manually.")

    default_selection = (
        tag_filtered_cities if (required_tags or excluded_tags)
        else ["Bali", "Barcelona", "Rio de Janeiro", "Bangkok", "Tenerife", "Maldives"]
    )

    selected_cities = st.multiselect(
        "Cities to compare",
        options=list(CITIES.keys()),
        default=default_selection,
    )

    if selected_cities:
        with st.expander("🔍 View city vibes", expanded=False):
            for city in selected_cities:
                tags = CITIES[city]["tags"]
                tag_pills = "  ".join(
                    f"{TAG_META[t]['icon']} {TAG_META[t]['label']}"
                    for t in sorted(tags) if t in TAG_META
                )
                st.caption(f"**{city}**: {tag_pills}")

# ── Step 3: Weather preferences ───────────────────────────────────────────────

# Defaults — overwritten by the sliders inside the expander when it's open
temp_range = (24, 32)
w_temp_n, w_rain_n, w_sun_n = 40, 35, 25

with st.expander("⚙️ Step 3 — Set your weather preferences", expanded=False):
    st.caption("Tell us what good weather means to you so we can rank destinations accurately.")
    temp_range = st.slider("Ideal temperature range (°C)", min_value=10, max_value=45, value=(24, 32))
    st.markdown("**What matters most to you?**")
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        w_temp = st.slider("🌡️ Temperature match", 0, 100, 40)
    with pc2:
        w_rain = st.slider("🌧️ Low rain probability", 0, 100, 35)
    with pc3:
        w_sun  = st.slider("☀️ Sunny days", 0, 100, 25)

    total_w = w_temp + w_rain + w_sun
    if total_w == 0:
        st.error("Weights can't all be zero.")
        st.stop()

    w_temp_n = round(w_temp / total_w * 100)
    w_rain_n = round(w_rain / total_w * 100)
    w_sun_n  = round(w_sun  / total_w * 100)
    st.caption(f"Normalised: 🌡️ {w_temp_n}%  ·  🌧️ {w_rain_n}%  ·  ☀️ {w_sun_n}%")

prefs = {
    "temp_min": temp_range[0], "temp_max": temp_range[1],
    "w_temp": w_temp_n, "w_rain": w_rain_n, "w_sun": w_sun_n,
}

if not selected_cities:
    st.warning("Select at least one city above to see results.")
    st.stop()

# ── Active filter summary ─────────────────────────────────────────────────────

if required_tags or excluded_tags:
    parts = []
    if required_tags:
        parts.append("✅ " + " · ".join(f"{TAG_META[t]['icon']} {TAG_META[t]['label']}" for t in sorted(required_tags)))
    if excluded_tags:
        parts.append("🚫 " + " · ".join(f"{TAG_META[t]['icon']} {TAG_META[t]['label']}" for t in sorted(excluded_tags)))
    st.caption("Active filters: " + "  |  ".join(parts))

# ── Ranked results ────────────────────────────────────────────────────────────

st.subheader("🏆 Ranked Destinations")

with st.spinner("Fetching live forecasts…"):
    results = []
    for city in selected_cities:
        info  = CITIES[city]
        daily = get_forecast(info["lat"], info["lon"], start.isoformat(), end.isoformat())
        if not daily or "temperature_2m_mean" not in daily:
            continue

        temps         = daily["temperature_2m_mean"]
        avg_temp      = round(sum(temps) / len(temps), 1)
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
    medal = medals[rank] if rank < 3 else f"#{rank + 1}"

    tag_display = "  ".join(
        f"{TAG_META[t]['icon']} {TAG_META[t]['label']}"
        for t in sorted(info.get("tags", set())) if t in TAG_META
    )

    with st.expander(
        f"{medal} **{city}** {info['flag']} {info['country']}  —  "
        f"Score: **{r['score']}/100**  ·  {wmo_label(s['dominant_code'])}  ·  "
        f"Avg {s['avg_temp']}°C  ·  {s['rainy_days']} rainy days",
        expanded=(rank == 0),
    ):
        if tag_display:
            st.caption(f"**Vibes:** {tag_display}")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Avg Temp",    f"{s['avg_temp']}°C")
        c2.metric("High / Low",  f"{s['max_temp']}° / {s['min_temp']}°")
        c3.metric("Total Rain",  f"{s['total_rain']} mm")
        c4.metric("Rain Chance", f"{s['avg_rain_prob']}%")
        c5.metric("Rainy Days",  f"{s['rainy_days']} / {s['total_days']}")

        daily = r["daily"]
        day_rows = [{
            "Date":    d,
            "Weather": wmo_label(daily["weathercode"][i]),
            "High °C": daily["temperature_2m_max"][i],
            "Low °C":  daily["temperature_2m_min"][i],
            "Rain mm": daily["precipitation_sum"][i],
            "Rain %":  daily["precipitation_probability_max"][i],
        } for i, d in enumerate(daily["time"])]

        st.dataframe(pd.DataFrame(day_rows).set_index("Date"), use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("🌡️ Temperature (°C)")
            st.line_chart(pd.DataFrame(
                {"High": daily["temperature_2m_max"], "Low": daily["temperature_2m_min"]},
                index=daily["time"]
            ))
        with col_b:
            st.caption("🌧️ Rain (mm)")
            st.bar_chart(pd.DataFrame({"Rain mm": daily["precipitation_sum"]}, index=daily["time"]))

# ── Full comparison table ─────────────────────────────────────────────────────

st.divider()
st.subheader("📊 Full Comparison")

table_rows = []
for rank, r in enumerate(results):
    s       = r["stats"]
    tag_str = " ".join(TAG_META[t]["icon"] for t in sorted(r["info"].get("tags", set())) if t in TAG_META)
    table_rows.append({
        "Rank":       medals[rank] if rank < 3 else f"#{rank + 1}",
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

# ── City confirmation & next step ─────────────────────────────────────────────

st.divider()
st.subheader("✅ Choose your destination")
st.caption("Happy with the rankings? Pick the city you want to go to and we'll take you straight to finding a hotel.")

ranked_city_names = [r["city"] for r in results]
default_city = st.session_state.get("selected_city", ranked_city_names[0] if ranked_city_names else None)

# Pre-select the top-ranked city, but let the user override
chosen_idx = ranked_city_names.index(default_city) if default_city in ranked_city_names else 0
chosen_city = st.selectbox(
    "Select your destination",
    options=ranked_city_names,
    index=chosen_idx,
    format_func=lambda c: f"{CITIES[c]['flag']} {c}, {CITIES[c]['country']}",
    key="city_confirm_select",
)

if st.button("🏨 Find hotels in " + chosen_city + " →", type="primary"):
    st.session_state["selected_city"] = chosen_city
    st.session_state["selected_city_flag"] = CITIES[chosen_city]["flag"]
    st.session_state["selected_city_country"] = CITIES[chosen_city]["country"]
    st.switch_page("pages/2_map.py")
