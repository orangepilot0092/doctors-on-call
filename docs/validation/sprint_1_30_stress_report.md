# Doctors on Call — Sprint 1–30 Stress Test Report

**Generated at:** 2026-10-06T12:52:27.196052+00:00

**Total tests:** 27
**Passed:** 27
**Failed:** 0
**Pass rate:** 100.00%

## Results

| Phase | Test | Status | Details |
|---|---|---|---|
| 00_Platform | API health check | PASS | {"status": "healthy", "service": "Doctors on Call"} |
| 01_Matching | Transit-aware deterministic matching | PASS | {"shift_id": 500, "total_matches": 15, "ranked_doctors": [{"doctor_id": 8, "doctor_code": "DOC-0008", "name": "Dr. Stress 8", "match_score": 200, "reasons": ["Specialty Match (ICU, Critical Care, Ventilator, ECMO)", "Tra |
| 01_Matching | pgvector semantic matching | PASS | {"query": "ICU Ventilator ECMO critical care", "total_matches": 5, "ranked_doctors": [{"id": 505, "doctor_code": "DOC-STRESS-505", "full_name": "Dr. Stress 505", "pg_specialty": "General Ward, Routine Care"}, {"id": 507, |
| 02_Concurrency | 10 doctors race for one shift; exactly 1 wins, 9 blocked | PASS | success=[501], conflict_count=9, other=[] |
| 03_Negotiation | Routine shift rejects 14k counter-offer | PASS | {"shift_id": 503, "urgency": "ROUTINE", "base_rate": 10000, "ai_evaluation": {"decision": "REJECTED", "message": "Sorry, the maximum authorized budget for this ROUTINE shift is \u20b911000.", "final_rate": 11000.0}} |
| 03_Negotiation | Critical shift accepts 14k counter-offer | PASS | {"shift_id": 504, "urgency": "CRITICAL", "base_rate": 10000, "ai_evaluation": {"decision": "ACCEPTED_WITH_BUFFER", "message": "Given the CRITICAL nature of this shift, we can accommodate \u20b914000.0.", "final_rate": 14 |
| 04_Handoff | AI medical handoff briefing endpoint | PASS | {"shift_id": 504, "facility_id": 4, "medical_briefing": {"status": "fallback_mode", "raw_notes": "Bed 4 is Mr. Sharma, 65yo COPD exacerbation on BiPAP, needs ABG at 9 PM, allergic to penicillin. Bed 5 is Mrs. Iyer, post- |
| 05_Lifecycle | Doctor 1 accepts Shift 501 | PASS | {"message": "Shift accepted successfully!", "shift_id": 501, "doctor_id": 1, "new_status": "ASSIGNED"} |
| 05_Lifecycle | Remote check-in blocked by geofence | PASS | {"detail": "\u274c Check-in REJECTED: You are 7047 meters away from JOY Hospital. You must be within 200 meters to check in."} |
| 05_Lifecycle | Local check-in accepted by geofence | PASS | {"message": "\u2705 Check-in successful! You are 18m from JOY Hospital.", "shift_id": 501, "check_in_time": "2026-10-06T12:52:25.924465+00:00"} |
| 05_Lifecycle | Remote check-out blocked by geofence | PASS | {"detail": "\u274c Check-out REJECTED: You are 7047 meters away. Please return to the hospital ward to check out."} |
| 05_Lifecycle | Local check-out completes shift | PASS | {"message": "\u2705 Shift completed! Payment processing initiated.", "shift_id": 501, "check_out_time": "2026-10-06T12:52:25.940194+00:00"} |
| 05_Lifecycle | Hospital funds escrow | PASS | {"message": "Hospital payment successful. Funds held in Escrow.", "details": {"status": "HELD", "razorpay_id": "pay_MOCK_12000_XYZ123", "amount": 12000.0}} |
| 05_Lifecycle | Instant payout triggered | PASS | {"message": "Instant payout triggered successfully via RazorpayX.", "details": {"status": "PAID_OUT", "doctor_payout": 10800.0, "platform_fee": 1200.0, "razorpay_payout_id": "payout_MOCK_10800_ABC", "fund_account_id": "f |
| 06_Ledger | Immutable ledger contains full money trail | PASS | ['FEE', 'HOLD', 'PAYMENT', 'PAYOUT', 'RELEASE'] |
| 07_Compliance | GST + TDS invoices generated correctly | PASS | {"platform_invoice": {"number": "INV-PLAT-BDE39E8E", "base": 1200.0, "gst": 216.0, "total": 1416.0}, "doctor_invoice": {"number": "INV-DOC-1186A563", "base": 10800.0, "tds_deducted": 216.0, "net_payout": 10584.0}} |
| 08_Dispute | Doctor 2 accepts Shift 502 | PASS | {"message": "Shift accepted successfully!", "shift_id": 502, "doctor_id": 2, "new_status": "ASSIGNED"} |
| 08_Dispute | Hospital funds escrow for Shift 502 | PASS | {"message": "Hospital payment successful. Funds held in Escrow.", "details": {"status": "HELD", "razorpay_id": "pay_MOCK_10000_XYZ123", "amount": 10000.0}} |
| 08_Dispute | Automatic no-show refund issued | PASS | {"dispute_id": 2, "status": "REFUNDED", "refund_amount": 10000.0, "message": "Doctor no-show confirmed. Full escrow refunded to hospital."} |
| 08_Dispute | Refund appears in immutable ledger | PASS | ['HOLD', 'PAYMENT', 'REFUND', 'REFUND_RECEIVED'] |
| 09_Trust | Trust score calculated for Doctor 1 | PASS | {"doctor_id": 1, "doctor_code": "DOC-00001", "doctor_name": "Dr. Rohan Sharma", "trust_score": 81, "completed_shifts": 8, "no_shows": 0, "late_check_ins": 0, "open_disputes": 0, "refunded_disputes": 0, "verification_appr |
| 09_Trust | Trust score calculated for Doctor 2 | PASS | {"doctor_id": 2, "doctor_code": "DOC-00002", "doctor_name": "Dr. Anita Desai", "trust_score": 0, "completed_shifts": 0, "no_shows": 2, "late_check_ins": 0, "open_disputes": 0, "refunded_disputes": 2, "verification_approv |
| 09_Trust | Reliable doctor ranks above no-show doctor | PASS | Doctor1=81, Doctor2=0 |
| 09_Trust | Trust leaderboard endpoint works | PASS | {"leaderboard": [{"doctor_id": 1, "doctor_code": "DOC-00001", "doctor_name": "Dr. Rohan Sharma", "status": "shift_ready", "trust_score": 81, "completed_shift_count": 8, "no_show_count": 0, "late_check_in_count": 0}, {"do |
| 10_Dashboard | Combined hospital dashboard returns all modules | PASS | {"roster_summary": {"total_shifts": 18, "filled_shifts": 9, "open_shifts": 9, "critical_open_shifts": 3, "fill_rate_percent": 50.0}, "total_gaps": 8, "metrics_keys": ["facility", "window_days", "total_shifts", "status_co |
| 11_Realtime | Facility live stream captured all key operational events | PASS | captured=['DISPUTE_OPENED', 'ESCROW_FUNDED', 'ESCROW_RELEASED', 'GPS_CHECK_IN', 'GPS_CHECK_OUT', 'PAYOUT_PROCESSED', 'REFUND_ISSUED', 'SHIFT_ACCEPTED'] |
| 11_Realtime | Global live stream captured trust update event | PASS | captured=['TRUST_UPDATED'] |

## Raw Live Stream Files

- `sse_facility_1_30.log`
- `sse_global_1_30.log`
