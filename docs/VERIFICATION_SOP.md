# 🏥 DOCTORS ON CALL — Doctor Verification SOP v1.0
**Standard Operating Procedure for Manual Verification**  
**Effective Date:** October 6, 2026  
**Target:** First 50 doctors (Concierge MVP)

---

## 🎯 Purpose

This SOP defines the **exact 14-point checklist** that must be completed for every doctor before they achieve VERIFIED status. No shortcuts. No exceptions.

**Principle:** "50 verified doctors > 5,000 unverified"

---

## 📋 The 14-Point Verification Checklist

### **PHASE 1: Identity Verification (Points 1-3)**

#### ☐ 1. Identity Verified
**What to verify:** Government-issued ID (Aadhaar, PAN, Passport, Driving License)

**Process:**
1. Doctor uploads clear photo of ID (front and back)
2. Operator visually inspects:
   - Photo matches doctor's profile photo
   - Name matches claimed name
   - DOB matches claimed DOB
   - ID not expired
   - No signs of tampering
3. Cross-check with selfie/video call if available
4. Record ID type, number, expiry date

**Evidence to capture:**
- Screenshot of ID (redact sensitive numbers except last 4)
- Operator notes
- Timestamp

**Pass criteria:** All visual checks pass, no red flags  
**Fail criteria:** Mismatch, tampering suspected, expired ID

---

#### ☐ 2. Name Match
**What to verify:** Name consistency across all documents

**Process:**
1. Compare name on:
   - Identity document
   - Medical registration certificate
   - MBBS certificate
   - PG certificate (if claimed)
   - Doctor's claimed name
2. Note any variations (middle name, initials, spelling)
3. If variations exist, request explanation document (gazette notification, marriage certificate, etc.)

**Evidence to capture:**
- Side-by-side comparison screenshot
- Notes on variations
- Explanation documents if any

**Pass criteria:** Names match or variations explained  
**Fail criteria:** Unexplained name mismatch

---

#### ☐ 3. Photo/Selfie Match
**What to verify:** Doctor's face matches identity documents

**Process:**
1. Doctor provides recent selfie or video call
2. Operator compares:
   - Face structure
   - Eyes, nose, mouth
   - Overall appearance
3. Note any significant differences (age, weight, etc.)
4. If unclear, request additional photo ID with photo

**Evidence to capture:**
- Selfie screenshot (with doctor's consent)
- Comparison notes
- Timestamp

**Pass criteria:** Clear facial match  
**Fail criteria:** Significant mismatch, suspected impersonation

---

### **PHASE 2: Medical Registration Verification (Points 4-7)**

#### ☐ 4. Medical Registration Number Verified
**What to verify:** Registration number is valid and belongs to this doctor

**Process:**
1. Doctor provides registration certificate
2. Extract registration number
3. Check against authoritative source:
   - **Maharashtra Medical Council (MMC):** https://mmcouncil.com/doctor-search/
   - **National Medical Commission (NMC):** https://nmc.org.in/medical-information-registry/indian-medical-register/
   - **Other State Councils:** As applicable
4. Confirm registration number exists in official database

**Evidence to capture:**
- Screenshot of official search result
- Registration number
- Source URL
- Timestamp of check

**Pass criteria:** Registration number found in official source  
**Fail criteria:** Number not found, mismatch

---

#### ☐ 5. Registration Authority Verified
**What to verify:** Registration is from recognized medical council

**Process:**
1. Identify issuing authority from certificate
2. Confirm authority is recognized by NMC
3. List of recognized councils: https://nmc.org.in/state-medical-councils/
4. Note council name, state, contact details

**Evidence to capture:**
- Council name
- Recognition status (confirmed/not found)
- Source URL

**Pass criteria:** Council is NMC-recognized  
**Fail criteria:** Council not recognized

---

#### ☐ 6. Registration Status Checked
**What to verify:** Registration is currently active and valid

**Process:**
1. Check status in official database:
   - Active / Valid
   - Suspended
   - Revoked
   - Expired
2. Note any conditions or restrictions
3. Check renewal date

**Evidence to capture:**
- Status screenshot
- Renewal date
- Any conditions noted

**Pass criteria:** Status is "Active" or "Valid"  
**Fail criteria:** Suspended, revoked, or expired

---

#### ☐ 7. Date Checked
**What to verify:** Verification is current (within policy timeframes)

**Process:**
1. Record exact date and time of verification
2. Set reminder for re-verification (12 months for registration)
3. Note in verification_events table

**Evidence to capture:**
- Timestamp (auto-generated)
- Re-verification date (calculated)

**Pass criteria:** Check completed today  
**Fail criteria:** N/A (this is a process step)

---

### **PHASE 3: Qualification Verification (Points 8-10)**

#### ☐ 8. MBBS Certificate Checked
**What to verify:** Doctor has valid MBBS degree from recognized institution

**Process:**
1. Doctor uploads MBBS certificate
2. Extract:
   - University/college name
   - Year of passing
   - Roll number / registration number
3. Verify university is NMC-recognized: https://nmc.org.in/medical-colleges-in-india/
4. Cross-check year of passing with registration date (should be after MBBS completion)
5. Look for signs of tampering

**Evidence to capture:**
- Certificate screenshot
- University name
- Year of passing
- Recognition status
- Operator notes

**Pass criteria:** Valid certificate from recognized university  
**Fail criteria:** Tampering suspected, unrecognized university, date mismatch

---

#### ☐ 9. PG Qualification Checked (If Claimed)
**What to verify:** Doctor has valid PG degree (MD/MS/DNB) if claimed

**Process:**
1. Doctor uploads PG certificate
2. Extract:
   - Degree type (MD/MS/DNB)
   - Specialty
   - University/institution
   - Year of completion
3. Verify institution is NMC-recognized
4. Cross-check with registration (specialty should match if registered as specialist)

**Evidence to capture:**
- Certificate screenshot
- Degree details
- Institution recognition status
- Operator notes

**Pass criteria:** Valid PG from recognized institution  
**Fail criteria:** Tampering, unrecognized institution, specialty mismatch

---

#### ☐ 10. Specialization Checked
**What to verify:** Claimed specialization matches credentials

**Process:**
1. If doctor claims specialization (ICU, Anesthesia, etc.):
   - Verify PG degree in that specialty
   - OR verify additional experience certificates
   - OR verify fellowship/certification
2. Cross-check with medical registration (if specialty registered)
3. Note level of expertise (PG degree vs. experience-based)

**Evidence to capture:**
- Specialization claimed
- Supporting documents
- Verification method
- Operator notes

**Pass criteria:** Specialization supported by credentials  
**Fail criteria:** No supporting evidence, mismatch

---

### **PHASE 4: Professional History (Point 11)**

#### ☐ 11. Experience Verified
**What to verify:** Doctor's claimed work history

**Process:**
1. Doctor provides experience certificates or reference contacts
2. For each claimed position:
   - Hospital/clinic name
   - Role
   - Duration
   - Department
3. Verify at least one of:
   - Experience certificate on hospital letterhead
   - Reference call to previous employer
   - LinkedIn profile (cross-check)
4. Note any gaps in employment

**Evidence to capture:**
- Experience certificates
- Reference call notes (if applicable)
- LinkedIn screenshot (if used)
- Operator notes

**Pass criteria:** Experience reasonably verified  
**Fail criteria:** Major discrepancies, unable to verify

---

### **PHASE 5: Administrative Verification (Points 12-14)**

#### ☐ 12. Bank/Payment Details Verified
**What to verify:** Doctor's bank account for payouts

**Process:**
1. Doctor provides:
   - Bank name
   - Account number
   - IFSC code
   - Account holder name
2. Verify account holder name matches doctor's name
3. Test with small payout (₹1) or use Razorpay verification API
4. Record details securely (encrypted)

**Evidence to capture:**
- Bank details (encrypted)
- Name match confirmation
- Test payout receipt (if applicable)

**Pass criteria:** Account verified, name matches  
**Fail criteria:** Name mismatch, account invalid

---

#### ☐ 13. Doctor Declaration Signed
**What to verify:** Doctor agrees to platform terms and declares accuracy

**Process:**
1. Doctor signs declaration (digital or physical):
   - All information provided is accurate
   - Will update platform of any changes
   - Will maintain valid registration
   - Will follow platform policies
   - Understands consequences of false information
2. Store signed declaration

**Evidence to capture:**
- Signed declaration (PDF or screenshot)
- Timestamp
- IP address (if digital)

**Pass criteria:** Declaration signed  
**Fail criteria:** Refusal to sign

---

#### ☐ 14. Onboarding Completed
**What to verify:** Doctor understands platform and is ready

**Process:**
1. Conduct onboarding call (15-30 minutes):
   - Explain platform
   - Demonstrate WhatsApp bot
   - Explain shift acceptance process
   - Explain payment terms
   - Answer questions
2. Collect emergency contact details
3. Confirm availability preferences
4. Answer all doctor's questions

**Evidence to capture:**
- Call notes
- Emergency contact details
- Availability preferences
- Timestamp

**Pass criteria:** Onboarding call completed, all questions answered  
**Fail criteria:** Doctor unresponsive, major concerns unresolved

---

## ✅ Final Approval

After all 14 points are completed:

1. **Senior Verification Officer** reviews entire file
2. Confirms all evidence is captured
3. Signs off in `verification_events` table
4. Changes status from REGISTERED → VERIFIED
5. Notifies doctor via WhatsApp

**Approval record:**
```json
{
  "doctor_id": "DOC-00001",
  "verification_type": "full_onboarding",
  "result": "approved",
  "verified_by": "operator_name",
  "verified_at": "2026-10-06T14:30:00Z",
  "checklist_completed": 14,
  "red_flags": 0,
  "notes": "All 14 points verified, no issues"
}
📊 Verification Metrics (Track These)
For the first 50 doctors, track:
Time to verify: Average hours from application to VERIFIED
Failure rate: % of applications that fail at each point
Common issues: Top 5 reasons for delays or rejections
Operator workload: Hours spent per verification
Target: <4 hours average verification time, <10% failure rate
🔄 After First 50: What to Automate
After manually verifying 50 doctors, analyze:
Which points are fastest to automate? (likely 4, 6, 8)
Which points need human judgment? (likely 1, 3, 11, 14)
What are the common failure patterns?
Then build automation for the repetitive parts, keep humans for judgment calls.
📝 Version History
v1.0 (October 6, 2026): Initial SOP for Concierge MVP
Next Review: After first 50 doctors verified
This SOP is the operational backbone of DOCTORS ON CALL's trust network. Follow it exactly.
