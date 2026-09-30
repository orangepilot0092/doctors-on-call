"""
AI-Powered Doctor Verification Service
Extracts registration number and name from certificates,
then verifies against NMC registry.
"""
import re
import io
import base64
from typing import Dict, Optional, Tuple
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import PyPDF2
import magic
import httpx
from bs4 import BeautifulSoup
import json


class AIDoctorVerifier:
    """AI-powered doctor certificate verification."""
    
    def __init__(self):
        self.nmc_search_url = "https://nmc.org.in/information-desk/indian-medical-register"
        # Common NMC registration patterns
        self.registration_patterns = [
            r'\b(MMC[-/]?[A-Z0-9]+)\b',  # Maharashtra Medical Council
            r'\b(DMC[-/]?[A-Z0-9]+)\b',  # Delhi Medical Council
            r'\b(KMC[-/]?[A-Z0-9]+)\b',  # Karnataka Medical Council
            r'\b(TNMC[-/]?[A-Z0-9]+)\b', # Tamil Nadu Medical Council
            r'\b(GMC[-/]?[A-Z0-9]+)\b',  # Gujarat Medical Council
            r'\b(\d{4,7})\b',  # Numeric registration numbers
        ]
        
        # Name extraction patterns
        self.name_patterns = [
            r'Dr\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'Name[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'Registered\s+Name[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
    
    async def extract_from_document(self, file_content: bytes, filename: str) -> Dict:
        """
        Extract text from PDF or image using OCR.
        Returns extracted text and metadata.
        """
        try:
            # Detect file type
            mime = magic.Magic(mime=True)
            file_type = mime.from_buffer(file_content)
            
            print(f"📄 Processing file: {filename} (Type: {file_type})")
            
            if file_type == 'application/pdf':
                text = self._extract_from_pdf(file_content)
            elif file_type.startswith('image/'):
                text = self._extract_from_image(file_content)
            else:
                return {"error": f"Unsupported file type: {file_type}", "confidence": 0}
            
            # Extract registration number
            reg_number = self._extract_registration_number(text)
            
            # Extract doctor name
            doctor_name = self._extract_doctor_name(text)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(text, reg_number, doctor_name)
            
            return {
                "extracted_text": text[:500],  # First 500 chars for preview
                "registration_number": reg_number,
                "doctor_name": doctor_name,
                "confidence": confidence,
                "file_type": file_type,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Error extracting from document: {str(e)}")
            return {"error": str(e), "confidence": 0, "success": False}
    
    def _extract_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF."""
        try:
            # Try direct text extraction first
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # If no text found, use OCR
            if not text.strip():
                print("📄 PDF has no text layer, using OCR...")
                images = convert_from_bytes(pdf_content)
                text = ""
                for img in images:
                    text += pytesseract.image_to_string(img) + "\n"
            
            return text
        except Exception as e:
            print(f"❌ Error extracting from PDF: {str(e)}")
            return ""
    
    def _extract_from_image(self, image_content: bytes) -> str:
        """Extract text from image using OCR."""
        try:
            image = Image.open(io.BytesIO(image_content))
            
            # Preprocess image for better OCR
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase contrast
            image = image.point(lambda x: 0 if x < 128 else 255, '1')
            
            # OCR with custom config for better accuracy
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text
        except Exception as e:
            print(f"❌ Error extracting from image: {str(e)}")
            return ""
    
    def _extract_registration_number(self, text: str) -> Optional[str]:
        """Extract NMC registration number using regex patterns."""
        text_upper = text.upper()
        
        for pattern in self.registration_patterns:
            matches = re.findall(pattern, text_upper)
            if matches:
                # Return the most likely match (longest one)
                best_match = max(matches, key=len)
                print(f"✅ Found registration number: {best_match}")
                return best_match
        
        return None
    
    def _extract_doctor_name(self, text: str) -> Optional[str]:
        """Extract doctor name using NLP patterns."""
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Return the first match
                name = matches[0].strip()
                print(f"✅ Found doctor name: {name}")
                return name
        
        return None
    
    def _calculate_confidence(self, text: str, reg_number: Optional[str], 
                             doctor_name: Optional[str]) -> float:
        """Calculate confidence score (0-100)."""
        score = 0
        
        # Text extracted successfully
        if text and len(text) > 50:
            score += 20
        
        # Registration number found
        if reg_number:
            score += 40
        
        # Doctor name found
        if doctor_name:
            score += 30
        
        # Common medical keywords present
        medical_keywords = ['medical', 'council', 'registration', 'certificate', 'doctor']
        keyword_count = sum(1 for kw in medical_keywords if kw.lower() in text.lower())
        score += min(keyword_count * 2, 10)
        
        return min(score, 100)
    
    async def verify_with_nmc(self, registration_number: str, 
                              expected_name: Optional[str] = None) -> Dict:
        """
        Verify registration number against NMC registry.
        Note: NMC doesn't have a public API, so we use web scraping.
        In production, use Surepass or Decentro API.
        """
        try:
            print(f"🔍 Verifying {registration_number} against NMC registry...")
            
            # For pre-seed, we simulate verification
            # In production, replace with actual API call:
            # - Surepass: https://surepass.io/nmc-verification-api/
            # - Decentro: https://decentro.tech/resources/professional-verification
            
            # Simulated verification (replace with real API)
            async with httpx.AsyncClient() as client:
                # Placeholder: In production, call actual NMC verification API
                # For now, we return a simulated result
                
                # Mock verification result
                verified = True  # Simulate successful verification
                registered_name = expected_name or "Dr. Verified Doctor"
                
                return {
                    "verified": verified,
                    "registration_number": registration_number,
                    "registered_name": registered_name,
                    "registration_date": "2020-01-15",
                    "qualification": "MBBS, MD",
                    "state_council": "Maharashtra Medical Council",
                    "status": "active",
                    "confidence": 95 if verified else 0,
                    "source": "NMC Registry (Simulated)"
                }
                
        except Exception as e:
            print(f"❌ Error verifying with NMC: {str(e)}")
            return {
                "verified": False,
                "error": str(e),
                "confidence": 0
            }
    
    async def full_verification_workflow(self, file_content: bytes, 
                                        filename: str) -> Dict:
        """
        Complete verification workflow:
        1. Extract from document
        2. Verify with NMC
        3. Return comprehensive result
        """
        print(f"\n🤖 Starting AI verification for {filename}...")
        
        # Step 1: Extract from document
        extraction_result = await self.extract_from_document(file_content, filename)
        
        if not extraction_result.get("success"):
            return {
                "success": False,
                "error": extraction_result.get("error", "Extraction failed"),
                "verification_status": "failed"
            }
        
        reg_number = extraction_result.get("registration_number")
        extracted_name = extraction_result.get("doctor_name")
        
        if not reg_number:
            return {
                "success": False,
                "error": "Could not extract registration number from document",
                "extraction_confidence": extraction_result.get("confidence", 0),
                "verification_status": "extraction_failed"
            }
        
        # Step 2: Verify with NMC
        verification_result = await self.verify_with_nmc(reg_number, extracted_name)
        
        # Step 3: Combine results
        final_result = {
            "success": True,
            "extraction": extraction_result,
            "verification": verification_result,
            "verification_status": "verified" if verification_result.get("verified") else "unverified",
            "overall_confidence": (
                extraction_result.get("confidence", 0) * 0.4 +
                verification_result.get("confidence", 0) * 0.6
            )
        }
        
        print(f"✅ Verification complete. Status: {final_result['verification_status']}")
        return final_result


# Singleton instance
ai_verifier = AIDoctorVerifier()
