import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://192.168.29.96:8000/api/v1"

st.set_page_config(
    page_title="Join DOCTORS ON CALL | Earn Extra Income",
    page_icon="👨‍⚕️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .hero-section h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .hero-section p {
        color: rgba(255,255,255,0.95);
        font-size: 1.3rem;
        margin: 1rem 0 0 0;
    }
    
    .benefit-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        height: 100%;
    }
    
    .benefit-card h3 {
        color: #667eea;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .benefit-card .icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 15px 30px;
        border-radius: 10px;
        border: none;
        font-size: 18px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 12px;
        font-size: 16px;
    }
    
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
    }
    
    .ai-badge {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1>👨‍⚕️ Join DOCTORS ON CALL</h1>
    <p>Earn ₹3,500 - ₹8,000 per shift | Pick your own schedule | Get paid in 48 hours</p>
</div>
""", unsafe_allow_html=True)

# Benefits Section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="benefit-card">
        <div class="icon">💰</div>
        <h3>Guaranteed Payment</h3>
        <p>Get paid within 48 hours of completing your shift. No more chasing clinics for payments.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="benefit-card">
        <div class="icon">📍</div>
        <h3>Work Near Home</h3>
        <p>Choose shifts within 10km of your location. No more traveling across Mumbai traffic.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="benefit-card">
        <div class="icon">⚡</div>
        <h3>Flexible Schedule</h3>
        <p>Pick up shifts when you're free. Work 1 day or 5 days a week - it's your choice.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Registration Form
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
st.markdown('<span class="ai-badge">🤖 AI-Powered Verification</span>', unsafe_allow_html=True)
st.markdown("### 📝 Doctor Registration")
st.markdown("Fill out your details below. Our AI will automatically extract and verify your NMC credentials from your certificate.")

with st.form("doctor_registration"):
    # Personal Information
    st.markdown("#### 👤 Personal Information")
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name (as per MBBS degree) *", placeholder="Dr. Priya Sharma")
        phone = st.text_input("WhatsApp Number *", placeholder="9876543210", max_chars=10)
    
    with col2:
        email = st.text_input("Email (optional)", placeholder="doctor@example.com")
        specialization = st.selectbox("Primary Specialization *", [
            "General Physician", "Pediatrician", "Gynecologist",
            "Orthopedic", "Dermatologist", "ENT", "Ophthalmologist",
            "Psychiatrist", "Cardiologist", "Other"
        ])
    
    # Location & Pricing
    st.markdown("#### 📍 Location & Pricing")
    col1, col2 = st.columns(2)
    
    with col1:
        base_location = st.text_input("Base Location *", placeholder="e.g., Vashi, Navi Mumbai")
        pincode = st.text_input("Your Area Pincode *", placeholder="400703", max_chars=6)
    
    with col2:
        daily_rate = st.number_input("Expected Daily Rate (₹) *", min_value=2000, max_value=15000, value=3500, step=500)
        preferred_zones = st.multiselect("Preferred Areas (optional)", [
            "Vashi", "Nerul", "Belapur", "Sanpada", "Kharghar", "Panvel",
            "Airoli", "Ghansoli", "Koparkhairane", "Andheri", "Bandra", "Dadar"
        ])
    
    # Document Upload
    st.markdown("#### 📄 NMC Certificate Upload")
    st.info("🤖 **AI-Powered:** Upload your NMC certificate and our AI will automatically extract your registration number and verify your credentials!")
    
    uploaded_file = st.file_uploader(
        "Upload NMC/Medical Council Registration Certificate *",
        type=["pdf", "jpg", "jpeg", "png"],
        help="Upload a clear photo or PDF of your NMC registration certificate"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Availability
    st.markdown("#### 📅 Availability (Next 7 Days)")
    st.write("Select the days you're available for locum shifts:")
    
    availability = {}
    today = datetime.now()
    
    cols = st.columns(7)
    for i, col in enumerate(cols):
        date = today + timedelta(days=i+1)
        date_str = date.strftime("%Y-%m-%d")
        day_name = date.strftime("%a %d")
        
        with col:
            is_available = st.checkbox(day_name, value=True, key=f"day_{i}")
            availability[date_str] = "free" if is_available else "busy"
    
    # Terms & Submit
    st.markdown("---")
    agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy *")
    
    submitted = st.form_submit_button("🚀 Join the Network (AI Verification)", use_container_width=True)
    
    if submitted:
        if not all([name, phone, base_location, pincode, specialization]):
            st.error("❌ Please fill in all required fields (marked with *)")
        elif not uploaded_file:
            st.error("❌ Please upload your NMC certificate")
        elif not agree_terms:
            st.error("❌ Please agree to the Terms of Service")
        else:
            with st.spinner("🤖 AI is extracting and verifying your credentials..."):
                # Prepare multipart form data
                files = {
                    "certificate": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                
                data = {
                    "name": name,
                    "phone": phone,
                    "email": email or "",
                    "specialization": specialization,
                    "base_location": base_location,
                    "pincode": pincode,
                    "daily_rate": str(daily_rate),
                    "preferred_zones": json.dumps(preferred_zones) if preferred_zones else None,
                    "availability_calendar": json.dumps(availability)
                }
                
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/doctors/register-with-document",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.balloons()
                        st.success("✅ Registration Successful!")
                        
                        # Show AI verification results
                        ai_result = result.get("ai_verification", {})
                        
                        with st.expander("🤖 AI Verification Results", expanded=True):
                            if ai_result.get("success"):
                                extraction = ai_result.get("extraction", {})
                                verification = ai_result.get("verification", {})
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**📄 Extracted Information:**")
                                    st.write(f"- **Registration Number:** {extraction.get('registration_number', 'Not found')}")
                                    st.write(f"- **Doctor Name:** {extraction.get('doctor_name', 'Not found')}")
                                    st.write(f"- **Confidence:** {extraction.get('confidence', 0)}%")
                                
                                with col2:
                                    st.markdown("**✅ NMC Verification:**")
                                    status = "✅ Verified" if verification.get('verified') else "⏳ Pending Manual Review"
                                    st.write(f"- **Status:** {status}")
                                    st.write(f"- **Registered Name:** {verification.get('registered_name', 'N/A')}")
                                    st.write(f"- **Confidence:** {verification.get('confidence', 0)}%")
                                
                                overall_confidence = ai_result.get("overall_confidence", 0)
                                st.progress(overall_confidence / 100)
                                st.write(f"**Overall Confidence: {overall_confidence:.0f}%**")
                            else:
                                st.warning(f"⚠️ AI extraction needs manual review: {ai_result.get('error', 'Unknown error')}")
                                st.info("Our team will manually verify your credentials within 24 hours.")
                        
                        st.markdown("""
                        <div class="custom-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white;">
                            <h3 style="color: white;">🎉 What Happens Next?</h3>
                            <p style="margin-top: 1rem; font-size: 1.1rem;">
                                1. ✅ Your credentials are being verified (24 hours)<br>
                                2. 📱 You'll receive a WhatsApp confirmation once approved<br>
                                3. 🏥 We'll notify you when shifts matching your profile are available<br>
                                4. 💰 Start earning within 48 hours of accepting your first shift!
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.error(f"❌ Registration failed: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to server. Please check your internet connection and try again.")
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# Testimonials Section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 💬 What Our Doctors Say")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="custom-card">
        <p style="font-style: italic;">"I earned ₹18,000 in just 4 shifts last month. The payment came in 48 hours - no chasing!"</p>
        <p style="margin-top: 1rem; font-weight: 600; color: #667eea;">— Dr. Rahul K., General Physician, Vashi</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="custom-card">
        <p style="font-style: italic;">"Finally, a platform that respects my time. I only get shifts within 5km of my home in Nerul."</p>
        <p style="margin-top: 1rem; font-weight: 600; color: #667eea;">— Dr. Priya S., Pediatrician, Nerul</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="custom-card">
        <p style="font-style: italic;">"The AI verification was instant. No more uploading the same documents to 10 different agencies."</p>
        <p style="margin-top: 1rem; font-weight: 600; color: #667eea;">— Dr. Amit P., Orthopedic, Belapur</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p><strong>DOCTORS ON CALL</strong> | India's First AI-Powered Medical Staffing Platform</p>
    <p>100+ Verified Doctors | 50+ Partner Clinics | Mumbai, Navi Mumbai & Thane</p>
    <p style="margin-top: 1rem; font-size: 0.85rem; color: #999;">
        © 2026 Doctors On Call. All rights reserved. | 
        <a href="#" style="color: #667eea;">Privacy Policy</a> | 
        <a href="#" style="color: #667eea;">Terms of Service</a>
    </p>
</div>
""", unsafe_allow_html=True)
