import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://192.168.29.96:8000/api/v1/pilot"

st.set_page_config(
    page_title="DOCTORS ON CALL | Instant Medical Staffing",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Card Styles */
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    
    .metric-card h3 {
        font-size: 2rem;
        margin: 0;
        font-weight: 700;
    }
    
    .metric-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Form Styles */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 12px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 12px;
        font-size: 16px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 12px 30px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Success Message */
    .success-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
    }
    
    .success-message h3 {
        color: white;
        margin: 0;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown("""
<div class="main-header">
    <h1>🩺 DOCTORS ON CALL</h1>
    <p>Instant, Verified Medical Staffing for Mumbai & Navi Mumbai</p>
</div>
""", unsafe_allow_html=True)

# Trust Indicators
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>⚡ 8 Min</h3>
        <p>Average Match Time</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>✅ 100%</h3>
        <p>NMC Verified Doctors</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>💳 48hrs</h3>
        <p>Guaranteed Payment</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Form Section
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
st.markdown("### 📋 Request a Doctor Shift")
st.markdown("Fill out the form below and our AI will match you with verified, available doctors in your area within minutes.")

with st.form("shift_request_form"):
    # Row 1
    col1, col2 = st.columns(2)
    with col1:
        clinic_name = st.text_input("🏥 Clinic / Hospital Name *", placeholder="e.g., City Care Clinic, Vashi")
        specialty = st.selectbox("👨‍⚕️ Required Specialty *", [
            "General Physician", "Pediatrician", "Gynecologist", 
            "Orthopedic", "Dermatologist", "Cardiologist", 
            "ENT Specialist", "Ophthalmologist", "Psychiatrist", "Other"
        ])
    
    with col2:
        clinic_pincode = st.text_input("📍 Clinic Pincode *", placeholder="e.g., 400703", max_chars=6)
        shift_date = st.date_input("📅 Shift Date *", min_value=datetime.now().date())
    
    # Row 2
    col3, col4 = st.columns(2)
    with col3:
        shift_time = st.selectbox("⏰ Shift Timing *", [
            "09:00 AM - 01:00 PM (Morning Half)",
            "02:00 PM - 06:00 PM (Evening Half)",
            "09:00 AM - 06:00 PM (Full Day)",
            "06:00 PM - 10:00 PM (Night Shift)",
            "Custom Timing"
        ])
        
        if shift_time == "Custom Timing":
            shift_time = st.text_input("Enter custom timing", placeholder="e.g., 10:00 AM - 02:00 PM")
    
    with col4:
        reason_posted = st.selectbox("❓ Reason for Request *", [
            "Doctor on planned leave",
            "Sudden illness / emergency",
            "Extra OPD load / high patient volume",
            "New specialty requirement",
            "Staff shortage",
            "Other"
        ])
        
        current_sourcing_method = st.selectbox("📱 How do you currently find doctors?", [
            "WhatsApp groups",
            "Personal network / referrals",
            "Traditional staffing agency",
            "Job portals",
            "Other"
        ])
    
    # Additional Info
    st.markdown("#### 💬 Additional Information (Optional)")
    additional_notes = st.text_area(
        "Any specific requirements or preferences?",
        placeholder="e.g., Need doctor with 5+ years experience, must speak Hindi and Marathi, parking available at clinic...",
        height=100
    )
    
    submitted = st.form_submit_button("🚀 Find Verified Doctors Now", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Form Submission Handler
if submitted:
    if not clinic_name or not clinic_pincode or not specialty:
        st.error("❌ Please fill in all required fields (marked with *)")
    elif len(clinic_pincode) != 6:
        st.error("❌ Please enter a valid 6-digit pincode")
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
        
        # Show processing animation
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("### 🤖 AI Matching in Progress...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate AI steps with professional messaging
        steps = [
            (15, "🔍 Validating shift requirements..."),
            (30, "🌍 Scanning verified doctors in your area..."),
            (50, "📊 Analyzing availability and specialization match..."),
            (70, "⭐ Ranking doctors by reliability and proximity..."),
            (85, "📱 Sending notifications to top matches..."),
            (100, "✅ Matching complete!")
        ]
        
        for percent, text in steps:
            time.sleep(1.2)
            progress_bar.progress(percent)
            status_text.markdown(f"**{text}**")
        
        # Call the actual FastAPI backend
        try:
            response = requests.post(f"{API_BASE_URL}/request-shift", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Success message
                st.balloons()
                st.markdown(f"""
                <div class="success-message">
                    <h3>✅ Shift Request Submitted Successfully!</h3>
                    <p style="margin-top: 1rem; font-size: 1.1rem;">
                        <strong>Shift ID:</strong> {data['id'][:8].upper()}<br>
                        <strong>Status:</strong> Matching in progress<br>
                        <strong>Expected Response:</strong> Within 30 minutes
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # What happens next
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)
                st.markdown("### 📋 What Happens Next?")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                    **Step 1: AI Matching** ⚡  
                    Our AI analyzes verified doctors in your area and matches based on specialty, availability, and proximity.
                    """)
                
                with col2:
                    st.markdown("""
                    **Step 2: Doctor Notification** 📱  
                    Top matched doctors receive WhatsApp notifications with shift details and can accept instantly.
                    """)
                
                with col3:
                    st.markdown("""
                    **Step 3: Confirmation** ✅  
                    You'll receive a confirmation with doctor details within 30 minutes. The doctor will arrive 15 minutes early.
                    """)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Founder Command Center (Demo Only)
                with st.expander("👀 Founder Command Center View (Demo Only)"):
                    st.info("This is what our operations team sees behind the scenes:")
                    st.code(f"""
🚨 NEW SHIFT REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Clinic: {clinic_name}
Pincode: {clinic_pincode}
Specialty: {specialty}
Date: {shift_date}
Time: {shift_time}

Status: AI Matching Complete
Action: Manual verification and WhatsApp notification
                    """, language="text")
                    
                    st.write("**Next Steps:**")
                    st.write("1. ✅ AI has identified 3 verified doctors in your area")
                    st.write("2. 📱 WhatsApp notifications sent to available doctors")
                    st.write("3. ⏳ Awaiting doctor acceptance (typically 5-15 minutes)")
                    st.write("4. 📞 Our team will call you once a doctor accepts")
            else:
                st.error(f"❌ Failed to submit request. Error: {response.text}")
                st.markdown('</div>', unsafe_allow_html=True)
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to our servers. Please check your internet connection and try again.")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)

# Footer Section
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div class="footer">
    <p><strong>DOCTORS ON CALL</strong> | Powered by AI | 100% NMC Verified Doctors</p>
    <p>Serving Mumbai, Navi Mumbai & Thane | 24/7 Support: +91-98765-43210</p>
    <p style="margin-top: 1rem; font-size: 0.85rem; color: #999;">
        © 2026 Doctors On Call. All rights reserved. | 
        <a href="#" style="color: #667eea;">Privacy Policy</a> | 
        <a href="#" style="color: #667eea;">Terms of Service</a>
    </p>
</div>
""", unsafe_allow_html=True)
