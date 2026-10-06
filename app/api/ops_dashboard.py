from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ops", tags=["Operator Dashboard"])

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOCTORS ON CALL — Verification Queue</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .verified { background-color: #d1fae5; color: #065f46; }
        .pending { background-color: #fef3c7; color: #92400e; }
        .rejected { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body class="bg-gray-100 font-sans p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">🏥 DOCTORS ON CALL</h1>
        <h2 class="text-xl text-gray-600 mb-8">Operator Verification Dashboard</h2>

        <div id="loading" class="text-center py-10 text-gray-500">Loading doctor profile...</div>

        <div id="doctor-profile" class="hidden bg-white p-6 rounded-lg shadow-md mb-8">
            <div class="flex justify-between items-center mb-4">
                <div>
                    <h3 id="doc-name" class="text-2xl font-bold"></h3>
                    <p id="doc-code" class="text-gray-500"></p>
                </div>
                <span id="doc-status" class="px-4 py-2 rounded-full text-sm font-bold uppercase"></span>
            </div>
            <div class="grid grid-cols-3 gap-4 text-sm text-gray-600">
                <div>📧 <span id="doc-email"></span></div>
                <div>📱 <span id="doc-phone"></span></div>
                <div>⭐ Trust Score: <span id="doc-score" class="font-bold"></span></div>
            </div>
        </div>

        <div id="checklist" class="hidden bg-white p-6 rounded-lg shadow-md">
            <h3 class="text-xl font-bold mb-4 text-gray-800">14-Point Verification SOP</h3>
            <ul id="sop-list" class="space-y-3"></ul>
        </div>
    </div>

    <script>
        const DOCTOR_ID = 1;
        const API_BASE = '/api/v1/verification';
        
        const SOP_POINTS = [
            { key: 'identity', label: '1. Identity Verified' },
            { key: 'name_match', label: '2. Name Match' },
            { key: 'photo_match', label: '3. Photo/Selfie Match' },
            { key: 'registration_number', label: '4. Medical Registration Number' },
            { key: 'registration_authority', label: '5. Registration Authority' },
            { key: 'registration_status', label: '6. Registration Status Active' },
            { key: 'date_checked', label: '7. Date Checked' },
            { key: 'mbbs_certificate', label: '8. MBBS Certificate Checked' },
            { key: 'pg_qualification', label: '9. PG Qualification Checked' },
            { key: 'specialization', label: '10. Specialization Checked' },
            { key: 'experience', label: '11. Experience Verified' },
            { key: 'bank_details', label: '12. Bank Details Verified' },
            { key: 'declaration', label: '13. Declaration Signed' },
            { key: 'onboarding', label: '14. Onboarding Completed' }
        ];

        async function loadDoctor() {
            try {
                // Fetch profile and history
                const profRes = await fetch(`${API_BASE}/doctors/${DOCTOR_ID}/profile`);
                const histRes = await fetch(`${API_BASE}/doctors/${DOCTOR_ID}/history`);
                
                if (!profRes.ok || !histRes.ok) throw new Error('Doctor not found');
                
                const profile = await profRes.json();
                const history = await histRes.json();

                // Render Profile
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('doctor-profile').classList.remove('hidden');
                document.getElementById('checklist').classList.remove('hidden');

                document.getElementById('doc-name').innerText = profile.full_name;
                document.getElementById('doc-code').innerText = profile.doctor_code;
                document.getElementById('doc-email').innerText = profile.email;
                document.getElementById('doc-phone').innerText = profile.phone;
                document.getElementById('doc-score').innerText = profile.trust_score || 'N/A';

                const statusEl = document.getElementById('doc-status');
                statusEl.innerText = profile.status.replace('_', ' ');
                statusEl.className = `px-4 py-2 rounded-full text-sm font-bold uppercase ${
                    profile.status === 'verified' ? 'bg-green-100 text-green-800' :
                    profile.status === 'shift_ready' ? 'bg-blue-100 text-blue-800' :
                    profile.status === 'suspended' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                }`;

                // Render Checklist
                const approvedTypes = new Set(
                    history.events
                        .filter(e => e.result === 'approved')
                        .map(e => e.verification_type)
                );
                const rejectedTypes = new Set(
                    history.events
                        .filter(e => e.result === 'rejected')
                        .map(e => e.verification_type)
                );

                const listEl = document.getElementById('sop-list');
                listEl.innerHTML = '';

                SOP_POINTS.forEach(point => {
                    let statusClass = 'bg-gray-50 text-gray-500 pending';
                    let icon = '⬜';
                    
                    if (approvedTypes.has(point.key)) {
                        statusClass = 'verified';
                        icon = '✅';
                    } else if (rejectedTypes.has(point.key)) {
                        statusClass = 'rejected';
                        icon = '❌';
                    }

                    const li = document.createElement('li');
                    li.className = `p-3 rounded-md flex justify-between items-center ${statusClass}`;
                    li.innerHTML = `<span class="font-medium">${icon} ${point.label}</span>`;
                    listEl.appendChild(li);
                });

            } catch (err) {
                document.getElementById('loading').innerText = `Error: ${err.message}. Did you seed the test doctor?`;
            }
        }

        loadDoctor();
    </script>
</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
async def operator_dashboard():
    """Serves the visual 14-point SOP checklist for operators."""
    return DASHBOARD_HTML
