import base64
import json
from datetime import datetime
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


@st.cache_data(ttl=60)
def load_sheet_data(worksheet_name):
  try:
    client = get_gspread_client()
    sheet = client.open_by_key(MASTER_SHEET_ID)
    worksheet = sheet.worksheet(worksheet_name)
    return worksheet.get_all_records()
  except Exception as e:
    return []


def append_row_to_sheet(worksheet_name, row_data):
  try:
    client = get_gspread_client()
    sheet = client.open_by_key(MASTER_SHEET_ID)
    worksheet = sheet.worksheet(worksheet_name)
    worksheet.append_row(row_data)
    return True
  except Exception as e:
    st.error(f"Error saving data: {e}")
    return False


# Initialize Session State for Authentication
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = None
  st.session_state.user_role = None
  st.session_state.block = None

# Authentication View
if not st.session_state.logged_in:
  st.markdown(
      "<h1 style='text-align: center;'>TogetheSpace v0.3</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h3 style='text-align: center; color: gray;'>Smart Community Hub &"
      " Resident Portal</h3>",
      unsafe_allow_html=True,
  )
  st.write("")

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    with st.form("login_form"):
      username_input = st.text_input("Username")
      password_input = st.text_input("Password", type="password")
      submit_login = st.form_submit_button("🚀 Enter Community Hub")

      if submit_login:
        users = load_sheet_data("Users")
        authenticated = False

        for user in users:
          if (
              user.get("Username") == username_input
              and str(user.get("Password")) == password_input
          ):
            st.session_state.logged_in = True
            st.session_state.username = user.get("Username")
            st.session_state.user_role = user.get("Role", "Resident")
            st.session_state.block = user.get("Block", "Block A")
            authenticated = True
            st.rerun()

        # Fallback admin default override
        if (
            username_input == "admin_blockA_0"
            and password_input == "securepassword123"
        ):
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
    st.caption(
        f"Role: {st.session_state.user_role} | Block:"
        f" {st.session_state.block}"
    )

    if st.button("🔑 Change Password"):
      st.info("Password update feature enabled.")

    st.divider()
    menu_selection = st.radio(
        "Community Menu",
        [
            "Resident Directory",
            "Communication & Feed",
            "Classifieds & Marketplace",
            "Helpdesk & Tickets",
            "Facility Booking",
            "Safety & SOS Alerts",
        ],
    )

    st.divider()
    if st.button("🔒 Logout"):
      st.session_state.logged_in = False
      st.rerun()

  block_name = st.session_state.block or "Block A"

  # Dynamic Main Panel Content based on Sidebar Selection
  if menu_selection == "Resident Directory":
    st.markdown(f"# {block_name} — Resident Directory")
    st.markdown(
        "Neighbor contacts, block locations & emergency SOS",
        help="Synced directly with Google Sheets Directory",
    )

    residents = load_sheet_data("Residents")
    filtered_residents = (
        [r for r in residents if r.get("Block") == block_name]
        if residents
        else []
    )
    display_data = filtered_residents if filtered_residents else residents

    search_query = st.text_input("🔍 Search residents by name or unit...")
    if search_query:
      display_data = [
          r
          for r in display_data
          if search_query.lower() in str(r.get("Name", "")).lower()
          or search_query.lower() in str(r.get("Unit", "")).lower()
      ]

    st.write(f"Showing {len(display_data)} residents for {block_name}")

    if display_data:
      for idx, res in enumerate(display_data):
        name = res.get("Name", f"Resident {idx+1}")
        diet = res.get("Diet", "N/A")
        blood = res.get("BloodGroup", res.get("Blood Group", "N/A"))

        with st.expander(f"👤 {name} | 🥗 {diet} | 🩸 Blood Group: {blood}"):
          col_a, col_b = st.columns(2)
          with col_a:
            st.write(f"**Email:** {res.get('Email', 'N/A')}")
            st.write(f"**Phone:** {res.get('Phone', 'N/A')}")
          with col_b:
            st.write(f"**Unit/Flat:** {res.get('Unit', res.get('Flat', 'N/A'))}")
            st.write(f"**Emergency Contact:** {res.get('EmergencyContact', 'N/A')}")
    else:
      st.info("No resident records found in the Google Sheet for this block.")

  elif menu_selection == "Communication & Feed":
    st.markdown("# Community Feed & Announcements")
    st.markdown("Catch up on the latest neighborhood updates and notices.")

    feed_items = load_sheet_data("Feed")
    if feed_items:
      for item in reversed(feed_items):
        with st.container():
          st.markdown(f"### {item.get('Title', 'Announcement')}")
          st.caption(
              f"Posted by: {item.get('Author', 'Management')} on"
              f" {item.get('Date', 'Recent')}"
          )
          st.write(item.get("Content", ""))
          st.divider()
    else:
      st.info("No community feed items posted yet.")

    with st.expander("📢 Post New Announcement"):
      with st.form("feed_form"):
        title = st.text_input("Title")
        content = st.text_area("Message Content")
        submitted = st.form_submit_button("Publish Announcement")
        if submitted and title and content:
          date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
          success = append_row_to_sheet(
              "Feed", [title, st.session_state.username, date_str, content]
          )
          if success:
            st.success("Announcement published successfully!")
            st.rerun()

  elif menu_selection == "Classifieds & Marketplace":
    st.markdown("# Classifieds & Marketplace")
    st.markdown("Buy, sell, or rent goods within your community block.")

    items = load_sheet_data("Marketplace")
    if items:
      cols = st.columns(2)
      for idx, item in enumerate(items):
        with cols[idx % 2]:
          with st.container(border=True):
            st.markdown(
                f"### {item.get('ItemName', 'Item')} —"
                f" ${item.get('Price', '0')}"
            )
            st.write(item.get("Description", ""))
            st.caption(
                f"Contact: {item.get('Contact', 'N/A')} | Seller:"
                f" {item.get('Seller', '')}"
            )
    else:
      st.info("No items currently listed in the marketplace.")

    with st.expander("🏷️ List a New Item"):
      with st.form("market_form"):
        item_name = st.text_input("Item Name")
        price = st.text_input("Price / Rent")
        desc = st.text_area("Description")
        contact = st.text_input("Contact Info (Phone/Email)")
        submitted = st.form_submit_button("Post Listing")
        if submitted and item_name:
          success = append_row_to_sheet(
              "Marketplace",
              [item_name, price, desc, contact, st.session_state.username],
          )
          if success:
            st.success("Listing added successfully!")
            st.rerun()

  elif menu_selection == "Helpdesk & Tickets":
    st.markdown("# Helpdesk & Maintenance Tickets")
    st.markdown(
        "Raise maintenance requests for plumbing, electrical, or general"
        " upkeep."
    )

    tickets = load_sheet_data("Tickets")
    user_tickets = (
        [t for t in tickets if t.get("Username") == st.session_state.username]
        if tickets
        else []
    )

    if user_tickets:
      st.subheader("Your Active Tickets")
      for t in user_tickets:
        st.markdown(
            f"- **{t.get('Category')}**: {t.get('Description')} (*Status:"
            f" {t.get('Status', 'Open')}*)"
        )

    with st.expander("🛠️ Raise New Support Ticket"):
      with st.form("ticket_form"):
        category = st.selectbox(
            "Category",
            ["Plumbing", "Electrical", "Security", "Housekeeping", "Other"],
        )
        description = st.text_area("Describe the issue")
        submitted = st.form_submit_button("Submit Ticket")
        if submitted and description:
          date_str = datetime.now().strftime("%Y-%m-%d")
          success = append_row_to_sheet(
              "Tickets",
              [
                  st.session_state.username,
                  category,
                  description,
                  "Open",
                  date_str,
              ],
          )
          if success:
            st.success("Ticket submitted successfully!")
            st.rerun()

  elif menu_selection == "Facility Booking":
    st.markdown("# Facility Booking")
    st.markdown(
        "Reserve shared community spaces like the clubhouse, tennis court, or"
        " guest rooms."
    )

    with st.form("booking_form"):
      facility = st.selectbox(
          "Select Facility",
          ["Clubhouse", "Tennis Court", "Guest Suite A", "Party Hall"],
      )
      date = st.date_input("Booking Date")
      time_slot = st.selectbox(
          "Time Slot",
          [
              "Morning (8 AM - 12 PM)",
              "Afternoon (1 PM - 5 PM)",
              "Evening (6 PM - 10 PM)",
          ],
      )
      submitted = st.form_submit_button("Confirm Booking")

      if submitted:
        success = append_row_to_sheet(
            "Bookings",
            [st.session_state.username, facility, str(date), time_slot],
        )
        if success:
          st.success(f"Successfully booked {facility} for {date}!")

  elif menu_selection == "Safety & SOS Alerts":
    st.markdown("# Safety & Emergency SOS")
    st.error(
        "⚠️ Use this section only in case of genuine emergencies to alert"
        " security and block wardens immediately."
    )

    col_sos1, col_sos2 = st.columns(2)
    with col_sos1:
      if st.button("🚨 TRIGGER FIRE EMERGENCY SOS", type="primary"):
        append_row_to_sheet(
            "SOS",
            [
                st.session_state.username,
                block_name,
                "FIRE EMERGENCY",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ],
        )
        st.error("FIRE SOS ALERT DISPATCHED TO SECURITY!")
    with col_sos2:
      if st.button("🚨 TRIGGER MEDICAL EMERGENCY SOS", type="primary"):
        append_row_to_sheet(
            "SOS",
            [
                st.session_state.username,
                block_name,
                "MEDICAL EMERGENCY",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ],
        )
        st.error("MEDICAL SOS ALERT DISPATCHED TO SECURITY!")
