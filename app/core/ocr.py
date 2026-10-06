import io
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

class OCRClient:
    def __init__(self):
        # Initialize the ONNX runtime engine
        self.engine = RapidOCR()

    def extract_text(self, file_bytes: bytes, mime_type: str) -> tuple[str, int]:
        """
        Extracts text from image bytes. 
        Returns a tuple of (extracted_text, confidence_score).
        """
        try:
            if mime_type.startswith('image/'):
                # Open image and convert to numpy array for RapidOCR
                img = Image.open(io.BytesIO(file_bytes)).convert('RGB')
                img_np = np.array(img)
                
                result, _ = self.engine(img_np)
                
                if not result:
                    return "", 0
                
                # result is a list of [box, text, confidence]
                text = "\n".join([line[1] for line in result])
                conf = int(sum([line[2] for line in result]) / len(result) * 100)
                return text, conf
            else:
                # For MVP, we only process images. PDF parsing requires poppler-utils.
                return "[PDF parsing skipped - upload JPG/PNG for automated OCR]", 0
        except Exception as e:
            return f"OCR Error: {str(e)}", 0

ocr_client = OCRClient()
