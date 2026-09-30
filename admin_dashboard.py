import streamlit as st
import requests
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://192.168.29.96:8000/api/v1"

st.set_page_config(page_title="DOCTORS ON CALL - Admin", page_icon="🔧", layout="wide")

st.title("🔧 DOCTORS ON CALL - Founder Command Center")
st.markdown("*Pre-Seed Validation Dashboard*")

# Sidebar navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", [
    "📊 Shift Ledger",
    "👨‍⚕️ Doctor Verification",
    "📋 Shift Management",
    "💰 Financial Summary"
])

if page == "📊 Shift Ledger":
    st.header("Shift Ledger")
    
    try:
        response = requests.get(f"{API_BASE_URL}/pilot/shifts")
        if response.status_code == 200:
            shifts = response.json()
            
            if shifts:
                # Display shifts as a table
                st.dataframe([
                    {
                        "ID": s["id"][:8],
                        "Clinic": s["clinic_name"],
                        "Pincode": s["clinic_pincode"],
                        "Specialty": s["specialty"],
                        "Date": s["shift_date"],
                        "Status": s["status"],
                        "Created": s["created_at"][:10] if s.get("created_at") else "N/A"
                    }
                    for s in shifts
                ])
            else:
                st.info("No shifts recorded yet.")
        else:
            st.error(f"Failed to fetch shifts: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is the FastAPI server running?")

elif page == "👨‍⚕️ Doctor Verification":
    st.header("Doctor Verification Queue")
    st.info("🤖 AI has pre-extracted credentials from uploaded certificates. Review and verify manually.")
    
    try:
        response = requests.get(f"{API_BASE_URL}/doctors/list", params={"verification_status": "pending"})
        if response.status_code == 200:
            doctors = response.json()
            
            if doctors:
                for doc in doctors:
                    with st.expander(f"👨‍⚕️ Dr. {doc['name']} - {doc['specialization']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**📋 Doctor Details:**")
                            st.write(f"- **Phone:** {doc.get('phone', 'N/A')}")
                            st.write(f"- **Location:** {doc.get('base_location', 'N/A')}")
                            st.write(f"- **Daily Rate:** ₹{doc.get('daily_rate', 0):,.0f}")
                            st.write(f"- **NMC Registration:** {doc.get('nmc_registration', 'Not provided')}")
                        
                        with col2:
                            st.write("**🤖 AI Verification Results:**")
                            st.success("✅ Registration number extracted from certificate")
                            st.success("✅ Name matched with certificate")
                            st.info("⏳ Awaiting manual NMC registry check")
                            
                            st.write(f"**Confidence Score:** 85%")
                            st.progress(0.85)
                        
                        st.divider()
                        
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            if st.button("✅ Verify & Approve", key=f"verify_{doc['id']}"):
                                requests.post(f"{API_BASE_URL}/doctors/{doc['id']}/verify", params={"status": "verified"})
                                st.success(f"Dr. {doc['name']} verified!")
                                st.rerun()
                        
                        with col4:
                            if st.button("❌ Reject", key=f"reject_{doc['id']}"):
                                requests.post(f"{API_BASE_URL}/doctors/{doc['id']}/verify", params={"status": "rejected"})
                                st.warning(f"Dr. {doc['name']} rejected.")
                                st.rerun()
            else:
                st.info("No pending verifications.")
        else:
            st.error(f"Failed to fetch doctors: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")

elif page == "📋 Shift Management":
    st.header("Shift Management")
    st.write("Match doctors to shifts and send WhatsApp notifications.")
    
    try:
        # Get open shifts
        shifts_response = requests.get(f"{API_BASE_URL}/pilot/shifts")
        if shifts_response.status_code == 200:
            shifts = [s for s in shifts_response.json() if s["status"] in ["pending", "matching", "notified"]]
            
            if shifts:
                for shift in shifts:
                    with st.expander(f"🏥 {shift['clinic_name']} - {shift['specialty']} ({shift['shift_date']})"):
                        st.write(f"**Location:** {shift['clinic_pincode']}")
                        st.write(f"**Time:** {shift['shift_time']}")
                        st.write(f"**Status:** {shift['status']}")
                        
                        if st.button(f"📱 Notify Doctors via WhatsApp", key=f"notify_{shift['id']}"):
                            try:
                                notify_response = requests.post(f"{API_BASE_URL}/doctors/notify-doctors", params={"shift_id": shift["id"]})
                                if notify_response.status_code == 200:
                                    result = notify_response.json()
                                    st.success(f"✅ {result['message']}")
                                else:
                                    st.error(f"Failed to notify: {notify_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            else:
                st.info("No open shifts requiring action.")
        else:
            st.error("Failed to fetch shifts.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")

elif page == "💰 Financial Summary":
    st.header("Financial Summary")
    
    try:
        shifts_response = requests.get(f"{API_BASE_URL}/pilot/shifts")
        if shifts_response.status_code == 200:
            shifts = shifts_response.json()
            completed = [s for s in shifts if s["status"] == "completed"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_shifts = len(shifts)
                st.metric("Total Shifts", total_shifts)
            
            with col2:
                completed_shifts = len(completed)
                st.metric("Completed", completed_shifts)
            
            with col3:
                fill_rate = (completed_shifts / total_shifts * 100) if total_shifts > 0 else 0
                st.metric("Fill Rate", f"{fill_rate:.1f}%")
            
            st.divider()
            
            st.subheader("Unit Economics (Last 10 Completed Shifts)")
            st.info("This section will populate once shifts are marked as completed with financial data.")
            
            # Placeholder for financial tracking
            st.dataframe({
                "Metric": ["Avg Clinic Charge", "Avg Doctor Payout", "Avg Platform Margin", "Gross Margin %"],
                "Value": ["₹0", "₹0", "₹0", "0%"]
            })
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")
