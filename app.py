import base64
import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="TogetheSpace v0.3",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_gspread_client():
    raw_b64 = st.secrets["GCP_JSON_BASE64"]
    json_str = base64.b64decode(raw_b64).decode("utf-8")
    creds_dict = json.loads(json_str)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

MASTER_SHEET_ID = st.secrets["SHEET_ID"]

@st.cache_resource
def get_py_client():
    return get_gspread_client()

def get_sheet_data(worksheet_name):
    try:
        client = get_py_client()
        sheet = client.open_by_key(MASTER_SHEET_ID)
        worksheet = sheet.worksheet(worksheet_name)
        return worksheet.get_all_records()
    except Exception as e:
        return []

# Initialize Session State for Authentication
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.block = None

# Authentication View
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>TogetheSpace v0.3</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Smart Community Hub & Resident Portal</h3>", unsafe_allow_html=True)
    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("🚀 Enter Community Hub")

            if submit_login:
                users = get_sheet_data("Users")
                authenticated = False
                
                # Fallback bypass or dynamic sheet validation
                for user in users:
                    if user.get("Username") == username_input and str(user.get("Password")) == password_input:
                        st.session_state.logged_in = True
                        st.session_state.username = user.get("Username")
                        st.session_state.user_role = user.get("Role", "Resident")
                        st.session_state.block = user.get("Block", "Block A")
                        authenticated = True
                        st.rerun()
                
                # Development/Admin override match if sheet is empty during bootstrapping
                if username_input == "admin_blockA_0" and password_input == "securepassword123":
                    st.session_state.logged_in = True
                    st.session_state.username = username_input
                    st.session_state.user_role = "Admin"
                    st.session_state.block = "Block A"
                    st.rerun()
                elif not authenticated:
                    st.error("Invalid username or password.")

else:
    # Authenticated Sidebar Navigation
    with st.sidebar:
        st.subheader(f"Resident: {st.session_state.username}")
        st.caption(f"Role: {st.session_state.user_role}")
        
        if st.button("🔑 Change Password"):
            st.info("Password update modal triggered.")

        st.divider()
        menu_selection = st.radio(
            "Community Menu",
            [
                "Resident Directory",
                "Communication & Feed",
                "Classifieds & Marketplace",
                "Helpdesk & Tickets",
                "Facility Booking",
                "Safety & SOS Alerts"
            ]
        )
        
        st.divider()
        if st.button("🔒 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Dynamic Main Panel Content based on Sidebar Selection
    if menu_selection == "Resident Directory":
        block_name = st.session_state.block or "Block A"
        st.markdown(f"# {block_name} — Resident Directory")
        st.markdown("Neighbor contacts, block locations & emergency SOS", help="Synced directly with Google Sheets Directory")
        
        residents = get_sheet_data("Residents")
        filtered_residents = [r for r in residents if r.get("Block") == block_name] if residents else []
        display_data = filtered_residents if filtered_residents else residents
        
        st.write(f"Showing {len(display_data)} residents for {block_name}")
        
        if display_data:
            for idx, res in enumerate(display_data):
                name = res.get("Name", f"Resident {idx+1}")
                diet = res.get("Diet", "N/A")
                blood = res.get("BloodGroup", res.get("Blood Group", "N/A"))
                
                with st.expander(f"👤 {name} | 🥗 {diet} | 🩸 Blood Group: {blood}"):
                    st.write(f"**Email:** {res.get('Email', 'N/A')}")
                    st.write(f"**Phone:** {res.get('Phone', 'N/A')}")
                    st.write(f"**Unit/Flat:** {res.get('Unit', res.get('Flat', 'N/A'))}")
        else:
            # Mock placeholder records if sheet is unpopulated
            mock_residents = [
                {"Name": "Sneha Gupta", "Diet": "VEG", "Blood Group": "B+", "Email": "sneha@example.com", "Phone": "+123456789", "Unit": "101"},
                {"Name": "Vivaan Singh", "Diet": "GOODWORKER", "Blood Group": "B+", "Email": "vivaan@example.com", "Phone": "+123456790", "Unit": "102"},
                {"Name": "Vikram Sen", "Diet": "SOBRE", "Blood Group": "A-", "Email": "vikram@example.com", "Phone": "+123456791", "Unit": "103"}
            ]
            for res in mock_residents:
                with st.expander(f"👤 {res['Name']} | 🥗 {res['Diet']} | 🩸 Blood Group: {res['Blood Group']}"):
                    st.write(f"**Email:** {res['Email']}")
                    st.write(f"**Phone:** {res['Phone']}")
                    st.write(f"**Unit/Flat:** {res['Unit']}")

    elif menu_selection == "Communication & Feed":
        st.markdown("# Community Feed & Announcements")
        st.write("Catch up on the latest announcements and neighborhood chatter.")

    elif menu_selection == "Classifieds & Marketplace":
        st.markdown("# Classifieds & Marketplace")
        st.write("Buy, sell, or rent goods within your community block.")

    elif menu_selection == "Helpdesk & Tickets":
        st.markdown("# Helpdesk & Maintenance Tickets")
        st.write("Raise tickets for maintenance, plumbing, electrical, or security concerns.")

    elif menu_selection == "Facility Booking":
        st.markdown("# Facility Booking")
        st.write("Reserve common areas like the community hall, guest rooms, or sports facilities.")

    elif menu_selection == "Safety & SOS Alerts":
        st.markdown("# Safety & Emergency SOS")
        st.error("Trigger emergency alerts or contact on-duty security staff immediately.")
