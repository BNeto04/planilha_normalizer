import json
import time

import requests
import streamlit as st

# --- API Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
CREDENTIALS_FILE = "credentials.json"

# --- Streamlit App ---
st.set_page_config(page_title="Google Sheets Pipeline", layout="wide")

st.title("Google Sheets Pipeline Controller")

# --- Helper Functions ---
def save_credentials(credentials_json: str):
    """Saves the provided JSON string to the credentials file."""
    try:
        # Validate if the content is valid JSON
        json.loads(credentials_json)
        with open(CREDENTIALS_FILE, "w") as f:
            f.write(credentials_json)
        st.success("Credentials saved successfully!")
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please paste the correct credentials.")
    except Exception as e:
        st.error(f"Failed to save credentials: {e}")


# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")
    spreadsheet_url = st.text_input("Enter Google Sheet URL")
    credentials_json = st.text_area(
        "Paste your Google Credentials JSON here",
        height=300,
        help="This will be saved as credentials.json in the local directory.",
    )

    if credentials_json:
        save_credentials(credentials_json)


# --- Main Content ---
st.header("Pipeline Controls")

if "sheets" not in st.session_state:
    st.session_state.sheets = []
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "job_status" not in st.session_state:
    st.session_state.job_status = "Not started"


col1, col2 = st.columns(2)

with col1:
    if st.button("List Sheets"):
        if not spreadsheet_url:
            st.warning("Please enter a spreadsheet URL.")
        else:
            try:
                with st.spinner("Fetching sheets..."):
                    response = requests.post(
                        f"{API_BASE_URL}/get-sheets",
                        json={"spreadsheet_url": spreadsheet_url},
                    )
                    response.raise_for_status()
                    data = response.json()
                    st.session_state.sheets = data.get("sheets", [])
                    st.success(f"Found {len(st.session_state.sheets)} sheets.")
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                if "response" in locals():
                    st.error(f"API Response: {response.text}")


    if st.session_state.sheets:
        selected_sheets = st.multiselect(
            "Select sheets to process",
            options=st.session_state.sheets,
            default=st.session_state.sheets, # Select all by default
        )

    if st.button("Execute Pipeline"):
        if not spreadsheet_url:
            st.warning("Please enter a spreadsheet URL.")
        elif "selected_sheets" not in locals() or not selected_sheets:
            st.warning("Please list and select sheets before executing.")
        else:
            try:
                with st.spinner("Starting pipeline..."):
                    payload = {
                        "spreadsheet_url": spreadsheet_url,
                        "source_sheets": selected_sheets,
                    }
                    response = requests.post(f"{API_BASE_URL}/run-from-url", json=payload)
                    response.raise_for_status()
                    job_info = response.json()
                    st.session_state.job_id = job_info.get("job_id")
                    st.session_state.job_status = job_info.get("status")
                    st.info(f"Pipeline started with Job ID: {st.session_state.job_id}")

            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                if "response" in locals():
                    st.error(f"API Response: {response.text}")


with col2:
    st.header("Job Status")
    if st.session_state.job_id:
        st.write(f"**Job ID:** `{st.session_state.job_id}`")

        progress_bar = st.progress(0)
        status_text = st.empty()

        while st.session_state.job_status in ["running", "submitted"]:
            try:
                response = requests.get(f"{API_BASE_URL}/status/{st.session_state.job_id}")
                response.raise_for_status()
                status_data = response.json()
                st.session_state.job_status = status_data.get("status")

                if st.session_state.job_status == "running":
                    status_text.info("Job is running...")
                    # Fake progress for visual feedback
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)

                elif st.session_state.job_status == "completed":
                    status_text.success("Job completed successfully!")
                    progress_bar.progress(100)
                    st.json(status_data.get("result"))
                    break # Exit polling loop

                elif st.session_state.job_status == "failed":
                    status_text.error("Job failed.")
                    progress_bar.progress(100)
                    st.error(status_data.get("result"))
                    break # Exit polling loop

                time.sleep(2) # Poll every 2 seconds

            except requests.exceptions.RequestException as e:
                status_text.error(f"Network error while polling status: {e}")
                break
            except Exception as e:
                status_text.error(f"Error polling status: {e}")
                if "response" in locals():
                    st.error(f"API Response: {response.text}")
                break
    else:
        st.info("No job has been started yet.")


st.divider()

st.header("Last Report")
if st.button("Consult Last Successful Report"):
    try:
        with st.spinner("Fetching last report..."):
            response = requests.get(f"{API_BASE_URL}/last-report")
            response.raise_for_status()
            report_data = response.json()
            st.success("Last report details:")
            st.json(report_data)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        if "response" in locals() and response.status_code == 404:
            st.warning("No completed reports found.")
        elif "response" in locals():
            st.error(f"API Response: {response.text}")