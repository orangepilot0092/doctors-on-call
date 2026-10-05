import streamlit as st
import requests
import time

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1/pilot"

st.set_page_config(page_title="DOCTORS ON CALL", page_icon="🩺", layout="centered")

# Custom CSS to make it look like a premium medical app
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #0056b3; color: white; font-weight: bold; width: 100%; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🩺 DOCTORS ON CALL")
st.markdown("### Clinic Staffing Portal")
st.markdown("Fill out the form below to request a verified locum doctor.")

with st.form("shift_request_form"):
    st.subheader("Shift Details")
    
    col1, col2 = st.columns(2)
    with col1:
        clinic_name = st.text_input("Clinic / Hospital Name", placeholder="e.g., City Care Clinic")
        specialty = st.selectbox("Required Specialty", [
            "General Physician", "Pediatrician", "Gynecologist", 
            "Orthopedic", "Dermatologist", "Cardiologist", "Other"
        ])
        shift_date = st.date_input("Shift Date")
    
    with col2:
        clinic_pincode = st.text_input("Clinic Pincode", placeholder="e.g., 400614", max_chars=6)
        shift_time = st.text_input("Shift Time", placeholder="e.g., 09:00 AM - 05:00 PM")
        reason_posted = st.selectbox("Reason for Request", [
            "Doctor on leave", "Sudden illness", "Extra OPD load", "New requirement", "Other"
        ])
    
    current_sourcing_method = st.selectbox("How do you currently find doctors?", [
        "WhatsApp groups", "Personal network", "Traditional agency", "Other"
    ])
    
    submitted = st.form_submit_button("🔍 Find Verified Doctors Now")

if submitted:
    if not clinic_name or not clinic_pincode:
        st.error("Please fill in the Clinic Name and Pincode.")
    else:
        # Prepare payload
        payload = {
            "clinic_name": clinic_name,
            "clinic_pincode": clinic_pincode,
            "specialty": specialty,
            "shift_date": str(shift_date),
            "shift_time": shift_time,
            "reason_posted": reason_posted,
            "current_sourcing_method": current_sourcing_method
        }
        
        # The "Wizard of Oz" Illusion
        st.success("Request submitted! Analyzing network...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate AI steps
        steps = [
            (10, f"Validating requirements for {specialty}..."),
            (30, f"Scanning verified doctors in pincode {clinic_pincode}..."),
            (60, "Checking real-time availability and travel distance..."),
            (80, "Ranking top matches based on reliability score..."),
            (100, "Matching complete. Notifying doctors...")
        ]
        
        for percent, text in steps:
            time.sleep(1.5) # 1.5s * 5 steps = 7.5 seconds (matches the 8s backend delay)
            progress_bar.progress(percent)
            status_text.text(text)
        
        # Call the actual FastAPI backend
        try:
            response = requests.post(f"{API_BASE_URL}/request-shift", json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                st.balloons()
                st.success(f"✅ **Success!** Shift ID: `{data['id'][:8]}...`")
                st.info("A verified doctor has been notified and will respond shortly. You will receive a confirmation once accepted.")
                
                # Show what the founder sees (for demo purposes)
                with st.expander("👀 Founder Command Center View (Demo Only)"):
                    st.write("Behind the scenes, the founder just received this Telegram alert:")
                    st.code(f"🚨 NEW SHIFT REQUEST\nClinic: {clinic_name}\nPincode: {clinic_pincode}\nSpecialty: {specialty}\nAction: Manual matching required.")
            else:
                st.error(f"Failed to submit request. Error: {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the server. Is the FastAPI backend running?")
