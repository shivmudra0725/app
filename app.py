import streamlit as st
import streamlit.components.v1 as components
import gspread
import requests
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# ----------------- Google Sheet Setup -----------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(".streamlit/credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Attendance Tracker")

today = datetime.now().strftime("%Y-%m-%d")
try:
    worksheet = spreadsheet.worksheet(today)
except:
    worksheet = spreadsheet.add_worksheet(title=today, rows="100", cols="10")
    worksheet.append_row(["Roll No", "Gmail", "Latitude", "Longitude", "Address", "Timestamp"])

# ----------------- UI -----------------
st.title("Smart Attendance System")

gmail = st.text_input("Enter your Gmail")
roll_options = [f"Roll-{i:02}" for i in range(1, 51)]  # Example: Roll-01 to Roll-50
roll_no = st.selectbox("Select your Roll Number", roll_options)

# JS to get location
components.html("""
<script>
navigator.geolocation.getCurrentPosition(
  (position) => {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    const coords = lat + "," + lon;
    window.parent.postMessage(coords, "*");
  }
)
</script>
""", height=0)

location = st.session_state.get("location", "")

# Listen for postMessage from iframe JS
if '_streamlit_location' not in st.session_state:
    st.session_state['_streamlit_location'] = ""

def location_listener():
    import streamlit.web.server.websocket_headers
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    from streamlit.runtime.runtime import Runtime
    ctx = get_script_run_ctx()
    runtime = Runtime.instance()
    session = runtime._session_mgr.get_session(ctx.session_id)
    if hasattr(session, "_uploaded_file_mgr"):  # hack to keep session alive
        session._uploaded_file_mgr
    return session

# This part won't work perfectly on all browsers; better to ask for input fallback
lat = st.text_input("Latitude")
lon = st.text_input("Longitude")

# Reverse Geocode using OpenStreetMap
address = "Not found"
if lat and lon:
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        resp = requests.get(url, headers={"User-Agent": "attendance-app"})
        address = resp.json().get("display_name", "Not found")
    except:
        pass

# ------------- Submit Attendance -------------
if st.button("Submit Attendance"):
    if not gmail.endswith("@gmail.com"):
        st.error("Please enter a valid Gmail.")
    elif not lat or not lon:
        st.error("Location not captured.")
    else:
        existing = [row[1] for row in worksheet.get_all_values()[1:]]  # get existing gmails
        if gmail in existing:
            st.warning("Attendance already submitted today.")
        else:
            worksheet.append_row([roll_no, gmail, lat, lon, address, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            st.success("Attendance submitted successfully!")
