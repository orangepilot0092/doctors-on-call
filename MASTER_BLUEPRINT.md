# 🏥 Doctors on Call (MUNDE / YUKTI AI) - Master Operational & Technical Blueprint
**Target Market:** Mumbai Metropolitan Region (MMR) - Mumbai, Navi Mumbai, Thane
**Stage:** Pre-Seed (Target: ₹1.5 Cr / $180k USD)
**Core Moat:** Agentic AI Orchestration + Native ABDM HPR Compliance + Transit-Aware Geospatial Routing

---

## 📊 1. Executive Pitch & Market Strategy
### The Problem
Hospitals in the MMR region rely on chaotic, fragmented WhatsApp groups to find locum RMOs, Intensivists, and Nurses for emergency shifts. Administrators waste hours verifying Maharashtra Medical Council (MMC) / Maharashtra Nursing Council (MNC) registrations manually. Furthermore, traditional apps fail to account for Mumbai's brutal transit reality—a doctor in Thane cannot reliably cover a last-minute shift in Andheri during peak hours, leading to massive "no-show" rates and compromised patient care.

### The Solution
An AI-Powered, Omnichannel Locum Marketplace.
* **For Hospitals (Web Portal):** Admins paste chaotic WhatsApp voice notes into our portal. Our **Entity Extraction Engine** instantly parses it into deterministic JSON and auto-creates a shift.
* **For Doctors/Nurses (WhatsApp/Telegram Bots):** Zero-friction UI. Doctors receive hyper-local, AI-matched shift alerts directly on WhatsApp and accept with a single tap.
* **The Compliance Moat:** Native integration with **Ayushman Bharat Digital Mission (ABDM) HPR APIs**. We automatically fetch, verify, and store credentials using RSA RS512 encryption, making every doctor 100% compliant by default.

### Business Model
* **Transaction Fee:** 12% - 15% commission on total shift payout.
* **Enterprise SaaS:** ₹25,000/month for large hospital chains for API access to our ABDM-compliant talent pool and predictive staffing analytics.

---

## ⚔️ 2. Competitor Landscape & Differentiation
The Indian healthcare staffing market is seeing a wave of VC-backed platforms, but they lack deep technical moats.

| Feature | Jobizo [[10]], [[23]] | DrLocum [[12]] | ProLocum [[13]] | **Doctors on Call (Us)** |
| :--- | :--- | :--- | :--- | :--- |
| **UI/UX for Doctors** | Mobile App Download | Mobile App Download | Mobile App Download | **WhatsApp / Telegram Bots (Zero friction)** |
| **Compliance / KYC** | Manual Uploads | Manual Verification | Manual Verification | **Native ABDM HPR API (Auto-verified via RSA)** |
| **Matching Logic** | Keyword Filters | Basic Location | Speed-focused (<5 mins) | **Agentic AI + Mumbai Transit/Train Line Logic** |
| **Hospital Input** | Rigid Web Forms | Structured Dashboards | Structured Dashboards | **NLP Entity Extraction from raw voice notes** |

**Global Benchmarks:** We are building the "Trusted Health" of India. Trusted Health raised $149M by focusing on AI-based job matching and eliminating manual credentialing [[20]]. We are applying this exact thesis to the MMR market using ABDM.

---

## 🏗️ 3. System Architecture & Design
### Core Tech Stack
* **Backend:** Python 3.12+, FastAPI, Pydantic V2, SQLAlchemy 2.x (Async)
* **Database:** PostgreSQL 15 + `pgvector` (for semantic skill matching)
* **Caching & Queues:** Redis 7 (Token caching, Celery message broker)
* **Object Storage:** MinIO (ABDM document caching, Base64 payloads)
* **Infrastructure:** Docker Compose, Poetry, Alembic (Async Migrations)

### The Agentic AI Orchestration Layer
1. **Entity Extraction Agent:** Parses chaotic text/voice-to-text into strict JSON schemas.
2. **Matching Agent:** Scores HCPs based on ABDM verification, proximity, and transit corridors.
3. **Compliance Agent:** Cross-references fetched ABDM data against shift requirements (MMC/MNC).
4. **Negotiation Agent:** Handles rate negotiations via WhatsApp within hospital budget constraints.

### ABDM HPR Integration Pipeline
* **Gateway Token:** UUID + ISO 8601 Timestamp + `X-CM-ID` headers, cached in Redis with a 60s expiry buffer.
* **Auth Flows:** Password, Aadhaar OTP, and Mobile OTP (using `cryptography` library for strict `RSA/ECB/PKCS1Padding`).
* **Data Sync:** Fetch Professional Details, Conditional Update Logic (`facilityDeclarationData`), and Base64 Document Uploads (1MB/5MB limits).

---

## 🗺️ 4. MMR Beachhead Operational Playbook
### Micro-Market Strategy
* **Mumbai (City & Suburbs):** High density of private nursing homes and corporate hospitals (Bandra, Andheri, South Mumbai). Focus on high-margin ICU/Intensivist shifts.
* **Navi Mumbai:** Rapidly expanding infrastructure (Kharghar, Vashi, Airoli). Focus on multi-specialty hospital rostering.
* **Thane:** Massive residential hub with mid-sized hospitals. High supply of RMOs and Nurses.

### Transit-Aware Routing Engine (The Geographic Moat)
Our matching algorithm does not use straight-line radius. It uses transit logic:
* **Western Line:** Andheri, Goregaon, Borivali.
* **Central Line:** Ghatkopar, Mulund, Thane.
* **Harbour Line:** Vashi, Nerul, Panvel.
* **Highways:** Sion-Panvel Highway, Eastern Express Highway (EEH), Trans-Harbour Link.
* *Rule:* A "CRITICAL" urgency shift will only ping doctors on the *exact same transit corridor* to guarantee arrival within 45 minutes.

---

## 🚀 5. The 50-Sprint Engineering Roadmap

### Phase 1: Core Infrastructure & ABDM Gateway (Sprints 1–5)
* **Sprint 1:** Monorepo, Poetry, Docker Compose (Postgres, Redis, MinIO), Core Schema.
* **Sprint 2:** ABDM Gateway Token Management (UUID, Timestamp, Redis Caching).
* **Sprint 3:** HPR Auth Flows (Password, Mobile OTP with RSA PKCS1v1.5, Aadhaar OTP).
* **Sprint 4:** Fetch/Update Professional Details & Document Management (Base64, 1MB/5MB limits).
* **Sprint 5:** HPR Contact Verification (Mobile & Email OTP Generate/Verify flows).

### Phase 2: Core Marketplace & Omnichannel UI (Sprints 6–10)
* **Sprint 6:** Entity Extraction Engine (Chaotic Text-to-Shift JSON parsing).
* **Sprint 7:** Hospital Web Portal (Shift CRUD, Roster Management).
* **Sprint 8:** WhatsApp Business API Integration (State machine for HCP onboarding).
* **Sprint 9:** Telegram Bot Fallback & Unified Message Broker (Celery/Redis).
* **Sprint 10:** Shift Matching & Notification Engine (Event bus for WhatsApp alerts).

### Phase 3: Agentic AI & Semantic Search (Sprints 11–15)
* **Sprint 11:** pgvector Integration (Semantic skill matching).
* **Sprint 12:** Compliance RAG Pipeline (MMC/MNC rule retrieval).
* **Sprint 13:** Conversational Negotiation Agent (WhatsApp rate haggling).
* **Sprint 14:** AI Shift Summarization & Handoff Briefings.
* **Sprint 15:** Supervisor Agent (LangGraph orchestration layer).

### Phase 4: Multi-Agent Orchestration (Sprints 16–20)
* **Sprint 16:** Matching Agent (Scoring based on ABDM status & transit).
* **Sprint 17:** Compliance Agent (Auto-rejecting expired registrations).
* **Sprint 18:** Scheduling & Routing Agent (Conflict resolution).
* **Sprint 19:** Dispute & Escrow Agent (Geofenced check-in verification).
* **Sprint 20:** Agent Fallback & Edge-Case Handling.

### Phase 5: Mumbai Geospatial Intelligence (Sprints 21–25)
* **Sprint 21:** Micro-Market Geofencing (OpenStreetMap integration).
* **Sprint 22:** Transit-Aware Routing Engine (Train lines & traffic corridors).
* **Sprint 23:** "Critical" Emergency Routing (5km / same transit line restriction).
* **Sprint 24:** Shift Check-in/Check-out Geofencing.
* **Sprint 25:** Supply/Demand Heatmap Analytics.

### Phase 6: Financials & Operations (Sprints 26–30)
* **Sprint 26:** Financial Engine (Hourly/Shift rates, night premiums).
* **Sprint 27:** Invoicing & Payout Generation (PDFs).
* **Sprint 28:** Payment Gateway & Escrow Integration (Razorpay/Cashfree).
* **Sprint 29:** Dispute Resolution UI (No-shows, early departures).
* **Sprint 30:** Financial Reporting Dashboard.

### Phase 7: Enterprise & Admin Dashboards (Sprints 31–35)
* **Sprint 31:** Hospital Portal - Locum Pool & Analytics.
* **Sprint 32:** Admin Dashboard - Agent Orchestration Monitor.
* **Sprint 33:** Admin Dashboard - ABDM API Health & Token Metrics.
* **Sprint 34:** Admin Dashboard - Geospatial Heatmaps.
* **Sprint 35:** Role-Based Access Control (RBAC) UI.

### Phase 8: Scale, Security & DPDP Act (Sprints 36–40)
* **Sprint 36:** Load Testing & Redis Caching Optimization.
* **Sprint 37:** DPDP Act 2023 Compliance (Consent archiving, Right to be Forgotten).
* **Sprint 38:** Immutable Audit Logging (ABDM data fetches).
* **Sprint 39:** Disaster Recovery & Automated Backups.
* **Sprint 40:** Penetration Testing & SOC2/ISO 27001 Readiness.

### Phase 9: Enterprise GTM & Expansion (Sprints 41–45)
* **Sprint 41:** Multi-Tenancy Architecture (Apollo/Fortis vs. standalone).
* **Sprint 42:** Developer Portal & API Marketplace (HMS/EMR integrations).
* **Sprint 43:** White-labeling Capabilities.
* **Sprint 44:** Advanced KPI Dashboards (Policy Discovery Time, AI Accuracy).
* **Sprint 45:** GTM Enablement (Sandbox data generators, sales collateral).

### Phase 10: Future-Proofing (Sprints 46–50)
* **Sprint 46:** Multilingual LLM Integration (Marathi/Hindi).
* **Sprint 47:** Geographic Expansion (Pune, Nagpur).
* **Sprint 48:** Knowledge Graph (HCP-Hospital-Specialty relationships).
* **Sprint 49:** Predictive Staffing AI (Monsoon dengue spikes, seasonal trends).
* **Sprint 50:** System Consolidation & Series A Due Diligence Prep.
