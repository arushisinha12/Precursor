import streamlit as st
import requests
import pandas as pd
import base64
import folium
from streamlit_folium import st_folium

API_URL = "http://localhost:8000"  # adjust if your backend runs elsewhere

st.set_page_config(page_title="Precursor Dashboard", layout="wide", page_icon="🔺")

# ---------- CLEAN PROFESSIONAL THEME ----------
st.markdown("""
    <style>
    .stApp {
        background-color: #fafafa;
    }
    h1 {
        color: #1a1a2e;
        font-weight: 800;
    }
    h2, h3, h4 {
        color: #16213e;
        font-weight: 700;
    }
    .stButton>button {
        background-color: #e63946;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.55rem 1.3rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #d62839;
        color: white;
    }
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 14px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    iframe {
        border-radius: 12px;
        border: 1px solid #d0d0d0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR: ROLE SELECTION ----------
st.sidebar.title("🔺 Precursor")
role = st.sidebar.radio("I am a:", ["User", "Organization"])

st.title("🔺 Precursor — Signals Before Incidents")
st.caption("Small reports gain meaning when they appear together.")

# ==================================================
# USER VIEW — Report & Map
# ==================================================
if role == "User":
    col_map, col_form = st.columns([2, 1])

    with col_map:
        st.subheader("Map")
        try:
            obs_response = requests.get(f"{API_URL}/observations/", timeout=5)
            observations = obs_response.json() if obs_response.status_code == 200 else []
        except requests.exceptions.RequestException:
            observations = []
            st.error("Could not reach backend. Is it running on localhost:8000?")

        default_lat, default_lng = 12.9353, 77.6246
        # Light, clean map tiles — clearly visible against white background
        m = folium.Map(location=[default_lat, default_lng], zoom_start=16, tiles="CartoDB positron")

        severity_colors = {1: "#2ecc71", 2: "#2ecc71", 3: "#f39c12", 4: "#e63946", 5: "#c81d25"}

        for obs in observations:
            lat = obs.get("latitude")
            lng = obs.get("longitude")
            severity = obs.get("severity", 1) or 1
            tags = obs.get("tags", [])
            desc = obs.get("description", "")
            color = severity_colors.get(severity, "gray")

            if lat and lng:
                folium.CircleMarker(
                    location=[lat, lng],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    weight=2,
                    popup=f"{', '.join(tags) if tags else 'untagged'} (severity {severity})<br>{desc}"
                ).add_to(m)

        st_folium(m, width=750, height=550)

    with col_form:
        st.subheader("Report an Observation")
        with st.form("report_form", clear_on_submit=True):
            description = st.text_area("What did you notice?")
            latitude = st.number_input("Latitude", value=12.9353, format="%.6f")
            longitude = st.number_input("Longitude", value=77.6246, format="%.6f")
            user_id = st.text_input("Your name/ID", value="anonymous")

            selected_tags = st.multiselect(
                "Tags (optional — AI will also detect these automatically)",
                options=[
                    "lighting", "electrical", "water", "plumbing", "structural",
                    "cleanliness", "overflow", "accessibility", "crowding",
                    "equipment", "safety", "other"
                ],
                help="You can manually flag categories, or leave blank and let the AI decide from your description."
            )

            photo_file = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png"])

            submitted = st.form_submit_button("Submit Observation")

            if submitted:
                photo_base64 = None
                if photo_file is not None:
                    photo_base64 = base64.b64encode(photo_file.read()).decode("utf-8")

                payload = {
                    "user_id": user_id,
                    "description": description,
                    "photo_base64": photo_base64,
                    "latitude": latitude,
                    "longitude": longitude,
                }

                # Send manually picked tags directly as "tags" so they actually
                # appear in the log (backend reads "tags", not "manual_tags")
                

                try:
                    resp = requests.post(f"{API_URL}/observations/", json=payload, timeout=30)
                    if resp.status_code in (200, 201):
                        result = resp.json()
                        tags = result.get("tags", [])
                        severity = result.get("severity", "N/A")
                        needs_review = result.get("needs_review", False)

                        st.success("Observation submitted and analyzed!")
                        st.markdown("**AI Analysis:**")
                        st.write(f"🏷️ Tags: {', '.join(tags) if tags else 'none detected'}")
                        st.write(f"⚠️ Severity: {severity}/5")
                        if needs_review:
                            st.warning("Flagged for human review (AI response was uncertain)")

                        st.button("Refresh map", on_click=st.rerun)
                    else:
                        st.error(f"Failed: {resp.status_code} — {resp.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {e}")

# ==================================================
# ORGANIZATION VIEW — Issue Log
# ==================================================
else:
    st.subheader("All Reported Issues (sorted by severity)")

    try:
        obs_response = requests.get(f"{API_URL}/observations/", timeout=5)
        observations = obs_response.json() if obs_response.status_code == 200 else []
    except requests.exceptions.RequestException:
        observations = []
        st.error("Could not reach backend.")

    if observations:
        df = pd.DataFrame(observations)

        show_needs_review_only = st.checkbox("🔍 Show only issues flagged for review")

        display_cols = [c for c in ["id", "timestamp", "user_id", "description", "tags", "severity", "needs_review", "cluster_id"] if c in df.columns]
        df = df[display_cols]

        if show_needs_review_only and "needs_review" in df.columns:
            df = df[df["needs_review"] == True]

        if "severity" in df.columns:
            df = df.sort_values(by="severity", ascending=False)

        st.caption("✅ Tick/untick the 'needs_review' box for any row to update it directly.")

        edited_df = st.data_editor(
            df,
            column_config={
                "needs_review": st.column_config.CheckboxColumn(
                    "Needs Review",
                    help="Toggle to mark this issue as reviewed or flag it for review",
                    default=False,
                ),
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "timestamp": st.column_config.TextColumn("Timestamp", disabled=True),
                "user_id": st.column_config.TextColumn("User", disabled=True),
                "description": st.column_config.TextColumn("Description", disabled=True),
                "tags": st.column_config.TextColumn("Tags", disabled=True),
                "severity": st.column_config.NumberColumn("Severity", disabled=True),
                "cluster_id": st.column_config.NumberColumn("Cluster", disabled=True),
            },
            disabled=["id", "timestamp", "user_id", "description", "tags", "severity", "cluster_id"],
            use_container_width=True,
            height=500,
            hide_index=True,
        )

        if st.button("💾 Save changes"):
            changes_made = 0
            for i in range(len(df)):
                original_val = df.iloc[i]["needs_review"]
                new_val = edited_df.iloc[i]["needs_review"]
                if original_val != new_val:
                    obs_id = df.iloc[i]["id"]
                    try:
                        patch_resp = requests.patch(
                            f"{API_URL}/observations/{obs_id}",
                            json={"needs_review": bool(new_val)},
                            timeout=10
                        )
                        if patch_resp.status_code in (200, 201):
                            changes_made += 1
                        else:
                            st.error(f"Failed to update observation {obs_id}: {patch_resp.status_code}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Request error for observation {obs_id}: {e}")

            if changes_made > 0:
                st.success(f"Updated {changes_made} observation(s)!")
                st.rerun()
            else:
                st.info("No changes to save.")

        if show_needs_review_only and len(df) == 0:
            st.info("No issues currently flagged for review.")
    else:
        st.info("No observations logged yet.")

    st.divider()
    st.subheader("Active Alerts (Clusters)")

    try:
        alerts_response = requests.get(f"{API_URL}/alerts/", timeout=5)
        alerts = alerts_response.json() if alerts_response.status_code == 200 else []
    except requests.exceptions.RequestException:
        alerts = []

    if alerts:
        alerts_df = pd.DataFrame(alerts)
        st.dataframe(alerts_df, use_container_width=True)
    else:
        st.info("No active alerts yet — need enough clustered reports to cross the threshold.")

    if st.button("🔄 Refresh"):
        st.rerun()