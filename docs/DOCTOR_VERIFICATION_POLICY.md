# 🏥 DOCTORS ON CALL — Doctor Verification Policy v1.0

**Effective Date:** October 6, 2026  
**Owner:** Head of Trust & Compliance  
**Review Cycle:** Quarterly

---

## 🎯 Purpose

This policy defines the **exact criteria** for doctor status transitions on the DOCTORS ON CALL platform. No engineer, operator, or executive may override these rules without documented exception approval.

**Core Principle:** A doctor's status is a **continuously maintained fact**, not a one-time decision.

---

## 📊 Doctor Status Definitions

### 🟡 REGISTERED
**Definition:** Doctor has created an account and submitted initial information, but verification is incomplete.

**Capabilities:**
- ❌ Cannot accept shifts
- ❌ Cannot receive shift alerts
- ✅ Can view platform information
- ✅ Can upload documents
- ✅ Can contact support

**Entry Criteria:**
- Account created via WhatsApp or Web Portal
- Basic profile information submitted (name, contact, claimed qualifications)
- At least one identity document uploaded

**Exit Criteria (to VERIFIED):**
- All 14 points of VERIFICATION_SOP.md completed
- Human reviewer signs off
- No red flags in evidence trail

**Time Limit:** If not verified within 30 days, account marked as STALE and requires re-onboarding.

---

### 🟢 VERIFIED
**Definition:** All mandatory credentials have been checked against authoritative sources and approved by a human reviewer.

**Capabilities:**
- ✅ Can receive shift alerts
- ✅ Can accept shifts (subject to Shift-Ready criteria)
- ✅ Visible to hospitals as "Verified"
- ✅ Can build reputation score

**Entry Criteria:**
- 100% completion of VERIFICATION_SOP.md
- All documents have evidence trail entries
- Human reviewer approval with timestamp
- No unresolved red flags

**Re-verification Requirement:**
- Medical registration: Checked every 12 months
- Identity: Checked every 24 months
- Qualifications: Checked only if new claims made

---

### 🔵 SHIFT-READY
**Definition:** Verified doctor who is operationally ready to accept and complete shifts immediately.

**Capabilities:**
- ✅ All VERIFIED capabilities
- ✅ Eligible for AI matching
- ✅ Can be matched to CRITICAL urgency shifts
- ✅ Visible in "Available Now" pool

**Entry Criteria:**
- VERIFIED status
- Availability confirmed (via WhatsApp or portal)
- Bank/payment details verified and tested
- Onboarding call completed
- Emergency contact verified
- No pending document renewals within 30 days
- Trust Score ≥ 70/100 (if applicable)

---

### 🔴 SUSPENDED
**Definition:** Doctor account temporarily deactivated pending investigation or resolution.

**Capabilities:**
- ❌ Cannot accept shifts
- ❌ Cannot receive shift alerts
- ❌ Not visible to hospitals
- ✅ Can contact support
- ✅ Can view suspension reason

**Entry Criteria (any of):**
- Red flag raised (fraud suspicion, complaint, incident)
- Credential expired and not renewed within 7 days
- Doctor requests pause
- No-show incident under investigation

---

### ⚫ EXPIRED
**Definition:** Doctor's verification has lapsed due to time or missing renewals.

**Entry Criteria:**
- VERIFIED or SHIFT-READY status
- Mandatory credential expired (registration, identity)
- 30-day grace period elapsed without renewal

**Exit Criteria:**
- Complete re-verification → return to VERIFIED
- 180 days expired → account archived, requires full re-onboarding

---

### ❌ REJECTED
**Definition:** Doctor application denied or account permanently terminated.

**Entry Criteria (any of):**
- Fraud detected (fake documents, identity mismatch)
- Medical registration revoked by council
- Serious incident (patient harm, legal action)
- Repeated policy violations

**Exit Criteria:**
- **None.** Permanent. Doctor may re-apply after 24 months with full disclosure.

---

## 🔐 Verification Authority

**Who can change status:**
- REGISTERED → VERIFIED: Senior Verification Officer
- VERIFIED → SHIFT-READY: Verification Officer + Operations
- Any → SUSPENDED: Trust & Safety Team (any member)
- SUSPENDED → previous: Head of Trust & Compliance
- Any → REJECTED: Head of Trust & Compliance + Legal review

**Audit Requirements:**
- Every status change logged in `verification_events` table
- Evidence attached to every event
- Immutable (no deletions, only new events)

---

## 📅 Continuous Verification Schedule

| Credential | Initial Check | Re-verification | Alert Before Expiry |
|------------|---------------|-----------------|---------------------|
| Identity | Onboarding | 24 months | 60 days |
| Medical Registration | Onboarding | 12 months | 90 days |
| MBBS Certificate | Onboarding | Only if new claim | N/A |
| PG Certificate | Onboarding | Only if new claim | N/A |
| Bank Details | Onboarding | 12 months | 30 days |
| Emergency Contact | Onboarding | 12 months | 30 days |
| Profile Photo | Onboarding | 24 months | 60 days |

---

## ⚠️ Red Flag Triggers (Auto-Suspension)

The system must auto-suspend and notify Trust & Safety when:
- Medical registration shows "revoked" or "suspended" in official source
- Identity mismatch detected during re-verification
- Document tampering suspected (hash mismatch)
- Multiple failed login attempts (>10 in 1 hour)
- Complaint from hospital (serious incident)
- Doctor reports lost/stolen credentials
- Legal notice received

---

## 📝 Policy Exceptions

Exceptions to this policy require:
1. Written request from Head of Department
2. Approval from Head of Trust & Compliance
3. Legal review if involves patient safety
4. Full documentation in audit trail
5. Quarterly review of all exceptions

---

## 🔄 Policy Review

- **Owner:** Head of Trust & Compliance
- **Review Cycle:** Quarterly
- **Last Review:** October 6, 2026
- **Next Review:** January 6, 2027
- **Version:** 1.0

---

*This policy is the foundation of DOCTORS ON CALL's trust network. Every engineer, operator, and executive must understand and follow it.*
