import re
import json
import httpx
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings

# ============================================================
# MUMBAI MMR KNOWLEDGE BASE
# ============================================================
# Sorted by length descending to ensure "Kharghar" matches before "Khar"
MUMBAI_AREAS = sorted([
    # Mumbai City & Central Suburbs
    "Colaba", "CST", "Fort", "Byculla", "Parel", "Dadar", "Matunga",
    "Sion", "Kurla", "Chembur", "Ghatkopar", "Bhandup", "Mulund", "Powai",
    # Western Suburbs
    "Bandra", "Khar", "Santacruz", "Vile Parle", "Andheri", "Jogeshwari",
    "Goregaon", "Malad", "Kandivali", "Borivali", "Dahisar",
    # Thane
    "Thane", "Kalwa", "Mumbra", "Dombivli", "Kalyan",
    # Navi Mumbai
    "Vashi", "Nerul", "Kharghar", "Airoli", "Ghansoli", "Sanpada",
    "Belapur", "Panvel", "Taloja",
], key=len, reverse=True)

HOSPITAL_MAPPING = {
    "kem": "KEM Hospital", "sion": "Sion Hospital", "nair": "Nair Hospital",
    "jj": "J.J. Hospital", "j.j.": "J.J. Hospital", "lilavati": "Lilavati Hospital",
    "nanavati": "Nanavati Hospital", "kokilaben": "Kokilaben Hospital",
    "hinduja": "Hinduja Hospital", "breach candy": "Breach Candy Hospital",
    "jaslok": "Jaslok Hospital", "apollo": "Apollo Hospital",
    "fortis": "Fortis Hospital", "wockhardt": "Wockhardt Hospital",
    "global": "Global Hospital", "jupiter": "Jupiter Hospital",
    "bethany": "Bethany Hospital", "horizon": "Horizon Hospital",
    "surana": "Surana Hospital", "holy family": "Holy Family Hospital",
    "bombay hospital": "Bombay Hospital", "saifee": "Saifee Hospital",
}

ROLE_MAPPING = {
    r'\bsister\b': "Staff Nurse", r'\bnurse\b': "Staff Nurse", r'\bstaff nurse\b': "Staff Nurse",
    r'\bnursing officer\b': "Staff Nurse", r'\bnursing staff\b': "Staff Nurse",
    r'\brmo\b': "RMO", r'\bresident\b': "RMO", r'\bresident medical officer\b': "RMO",
    r'\bduty doctor\b': "RMO", r'\bdmo\b': "RMO",
    r'\bintensivist\b': "Intensivist", r'\bicu doctor\b': "Intensivist",
    r'\bcritical care doctor\b': "Intensivist",
    r'\bconsultant\b': "Consultant", r'\bspecialist\b': "Consultant",
    r'\bsenior doctor\b': "Consultant", r'\battending\b': "Consultant",
    r'\btechnician\b': "Technician", r'\btech\b': "Technician", r'\bot tech\b': "Technician",
    r'\blab tech\b': "Technician", r'\bradiographer\b': "Technician",
}

DEPARTMENT_MAPPING = {
    r'\bicu\b': "ICU", r'\bintensive care\b': "ICU", r'\bcritical care\b': "ICU",
    r'\bnicu\b': "NICU", r'\bneonatal icu\b': "NICU", r'\bneonatal\b': "NICU",
    r'\bpicu\b': "PICU", r'\bpediatric icu\b': "PICU",
    r'\bcasualty\b': "ER", r'\bemergency\b': "ER", r'\ber\b': "ER", r'\baccident\b': "ER",
    r'\bward\b': "General Ward", r'\bgeneral ward\b': "General Ward",
    r'\bot\b': "OT", r'\boperation theatre\b': "OT", r'\boperation theater\b': "OT",
    r'\bdialysis\b': "Dialysis", r'\bcath lab\b': "Cath Lab",
}

URGENCY_CRITICAL = [
    r'\bimmediate\b', r'\bemergency\b', r'\burgent\b', r'\bcritical\b', r'\bdoctor left\b',
    r'\babsent\b', r'\bstuck in traffic\b', r'\bno show\b', r"\bno-show\b", r"\bdidn't come\b",
    r'\bsuddenly\b', r'\bpatient rush\b', r'\bovercrowded\b', r'\basap\b', r'\bright now\b',
]

URGENCY_HIGH = [
    r'\bneed urgently\b', r'\bhigh priority\b', r'\bsoon\b', r'\btoday\b', r'\btonight\b',
    r'\btomorrow\b', r'\bthis week\b', r'\bshort notice\b', r'\bquickly\b', r'\bfast\b',
]

SPECIALTY_KEYWORDS = {
    r'\bpediatrics\b': "Pediatrics", r'\bpaediatrics\b': "Pediatrics", r'\bchild\b': "Pediatrics",
    r'\bcardiology\b': "Cardiology", r'\bcardiac\b': "Cardiology", r'\bheart\b': "Cardiology",
    r'\borthopedics\b': "Orthopedics", r'\bortho\b': "Orthopedics",
    r'\bneurology\b': "Neurology", r'\bneuro\b': "Neurology",
    r'\bgynecology\b': "Gynecology", r'\bgynae\b': "Gynecology", r'\bobstetrics\b': "Obstetrics",
    r'\boncology\b': "Oncology", r'\bcancer\b': "Oncology",
    r'\bnephrology\b': "Nephrology", r'\bkidney\b': "Nephrology",
    r'\bpulmonology\b': "Pulmonology", r'\brespiratory\b': "Pulmonology",
    r'\bgastroenterology\b': "Gastroenterology", r'\bgastro\b': "Gastroenterology",
    r'\banesthesia\b': "Anesthesiology", r'\banaesthesia\b': "Anesthesiology",
    r'\bpsychiatry\b': "Psychiatry", r'\bdermatology\b': "Dermatology", r'\bent\b': "ENT",
    r'\bophthalmology\b': "Ophthalmology", r'\beye\b': "Ophthalmology",
    r'\burology\b': "Urology", r'\bradiology\b': "Radiology", r'\bpathology\b': "Pathology",
}

EXTRACTION_PROMPT = """You are an expert medical staffing coordinator for Mumbai, India.
Extract structured shift information from chaotic hospital messages. Return ONLY valid JSON.
Input: "{text}"
"""


class ShiftExtractionEngine:
    def extract(self, text: str) -> Dict[str, Any]:
        result = self._rule_based_extract(text)
        if settings.LLM_ENABLED:
            try:
                llm_result = self._llm_extract_sync(text)
                result = self._merge_results(result, llm_result)
            except Exception:
                pass
        return result

    def _rule_based_extract(self, text: str) -> Dict[str, Any]:
        t = text.lower()
        role = self._extract_role(t)
        department = self._extract_department(t)
        location = self._extract_location(t)
        urgency = self._extract_urgency(t)
        rate, rate_basis = self._extract_rate(t)
        shift_type = self._extract_shift_type(t)
        hours = self._extract_hours(t)
        gender = self._extract_gender(t)
        registration = self._extract_registration(t, role)
        specialty = self._extract_specialty(t)
        date_raw = self._extract_date(text)
        hospital_name = self._extract_hospital(t)

        return {
            "hospital_metadata": {"name": hospital_name, "location_area": location, "department": department},
            "shift_details": {"role_required": role, "specialty": specialty, "date_raw": date_raw, "shift_type": shift_type, "estimated_hours": hours, "urgency_level": urgency},
            "financials": {"offered_rate_inr": rate, "rate_basis": rate_basis},
            "compliance_flags": {"required_registration": registration, "gender_preference": gender},
        }

    def _extract_role(self, t: str) -> Optional[str]:
        for pattern, role in ROLE_MAPPING.items():
            if re.search(pattern, t): return role
        if re.search(r'\bdoctor\b', t): return "RMO"
        return None

    def _extract_department(self, t: str) -> Optional[str]:
        for pattern, dept in DEPARTMENT_MAPPING.items():
            if re.search(pattern, t): return dept
        return None

    def _extract_location(self, t: str) -> Optional[str]:
        for area in MUMBAI_AREAS:
            if re.search(r'\b' + re.escape(area.lower()) + r'\b', t):
                return area
        return None

    def _extract_hospital(self, t: str) -> Optional[str]:
        for keyword, name in HOSPITAL_MAPPING.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', t):
                return name
        return None

    def _extract_urgency(self, t: str) -> str:
        for pattern in URGENCY_CRITICAL:
            if re.search(pattern, t): return "CRITICAL"
        for pattern in URGENCY_HIGH:
            if re.search(pattern, t): return "HIGH"
        return "ROUTINE"

    def _extract_rate(self, t: str) -> Tuple[Optional[int], Optional[str]]:
        rate_match = re.search(r'(?:rs\.?|₹|inr)?\s*(\d{3,6})\s*(?:/-)?', t)
        if not rate_match: return None, None
        rate = int(rate_match.group(1))
        if any(re.search(p, t) for p in [r'\bper hour\b', r'\bper hr\b', r'\b/hour\b', r'\b/hr\b', r'\bhourly\b']): return rate, "per_hour"
        if any(re.search(p, t) for p in [r'\bper shift\b', r'\b/shift\b', r'\bper duty\b', r'\bflat\b', r'\blumpsum\b']): return rate, "per_shift"
        if any(re.search(p, t) for p in [r'\bper day\b', r'\b/day\b', r'\bdaily\b']): return rate, "per_day"
        return rate, None

    def _extract_shift_type(self, t: str) -> Optional[str]:
        if re.search(r'\bnight\b', t): return "Night"
        if re.search(r'\bday shift\b|\bday duty\b|\bmorning\b', t): return "Day"
        if re.search(r'\b24\s*hour\b|\b24hr\b|\bfull day\b', t): return "24-Hour"
        return None

    def _extract_hours(self, t: str) -> Optional[int]:
        match = re.search(r'(\d{1,2})\s*(?:hour|hr|hrs|hours)', t)
        return int(match.group(1)) if match else None

    def _extract_gender(self, t: str) -> str:
        if re.search(r'\bfemale\b|\blady\b|\bwoman\b', t): return "Female"
        if re.search(r'\bmale only\b|\bmale candidate\b', t): return "Male"
        return "None"

    def _extract_registration(self, t: str, role: Optional[str]) -> Optional[str]:
        if re.search(r'\bmmc\b|\bmedical council\b', t): return "MMC"
        if re.search(r'\bmnc\b|\bnursing council\b', t): return "MNC"
        if role in ["RMO", "Consultant", "Intensivist"]: return "MMC"
        if role == "Staff Nurse": return "MNC"
        return None

    def _extract_specialty(self, t: str) -> Optional[str]:
        for pattern, specialty in SPECIALTY_KEYWORDS.items():
            if re.search(pattern, t): return specialty
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        t_lower = text.lower()
        patterns = [r'\b(today|tomorrow|tonight)\b', r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{0,4})\b', r'\b((?:mon|tue|wed|thu|fri|sat|sun)[a-z]*)\b', r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b']
        for pattern in patterns:
            match = re.search(pattern, t_lower)
            if match: return match.group(1).strip()
        return None

    def _llm_extract_sync(self, text: str) -> Dict[str, Any]:
        prompt = EXTRACTION_PROMPT.format(text=text)
        headers = {"Content-Type": "application/json"}
        if settings.LLM_API_KEY: headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
        payload = {"model": settings.LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": settings.LLM_TEMPERATURE, "max_tokens": settings.LLM_MAX_TOKENS}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{settings.LLM_BASE_URL}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"): content = re.sub(r'^```(?:json)?\s*', '', content); content = re.sub(r'\s*```$', '', content)
            return json.loads(content)

    def _merge_results(self, base: Dict, llm: Dict) -> Dict:
        merged = json.loads(json.dumps(base))
        for section in ["hospital_metadata", "shift_details", "financials", "compliance_flags"]:
            if section in llm and isinstance(llm[section], dict):
                for key, value in llm[section].items():
                    if value is not None: merged[section][key] = value
        return merged

extraction_engine = ShiftExtractionEngine()
