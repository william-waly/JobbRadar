import pandas as pd
import requests
import streamlit as st
import os

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="JobbRadar", layout="wide")
st.title("JobbRadar – Job Market Intelligence")


@st.cache_data(ttl=60)
def fetch(path: str, params: dict | None = None):
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


try:
    stats = fetch("/statistics")
except requests.RequestException:
    st.error("Får ikke kontakt med API-et. Kjører `uvicorn app.api.main:app` i en annen terminal?")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Totalt antall jobber", stats["total_jobs"])
col2.metric("Antall selskaper", stats["total_companies"])
col3.metric("Antall unike skills", stats["total_skills"])

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Mest etterspurte skills")
    skills = fetch("/statistics/skills", params={"limit": 10})
    if skills:
        skills_df = pd.DataFrame(skills).set_index("skill")
        st.bar_chart(skills_df["count"])
    else:
        st.info("Ingen skills-data ennå.")

with right:
    st.subheader("Jobber per lokasjon")
    locations = fetch("/statistics/locations", params={"limit": 10})
    if locations:
        locations_df = pd.DataFrame(locations).set_index("location")
        st.bar_chart(locations_df["count"])
    else:
        st.info("Ingen lokasjonsdata ennå.")

st.divider()
st.subheader("Jobbannonser")

jobs = fetch("/jobs", params={"limit": 50})
if jobs:
    jobs_df = pd.DataFrame(
        [
            {
                "Tittel": j["title"],
                "Selskap": j["company"]["name"],
                "Sted": j["location"],
                "Kategori": j["category"],
                "Senioritet": j["seniority"],
            }
            for j in jobs
        ]
    )
    st.dataframe(jobs_df, use_container_width=True)
else:
    st.info("Ingen jobber å vise ennå.")