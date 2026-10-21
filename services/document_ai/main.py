"""
Document AI Service - FastAPI
Member 2 - Document Extraction and OCR
Extracts structured information from RC, insurance, and service documents
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pytesseract
from PIL import Image
import io
import json
import uuid
from datetime import datetime
import os
import threading
import importlib.util

app = FastAPI(
    title="CarVal Document AI Service",
    description="OCR and document extraction for vehicle documents",
    version="0.1.0"
)


class DocumentField(BaseModel):
    """Extracted field from document"""
    name: str
    value: Optional[Any] = None
    confidence: float = 0.0


class RCResponse(BaseModel):
    """Registration Certificate extraction response"""
    document_type: str = "rc"
    extracted: bool
    confidence: float
    fields: Dict[str, Any]
    source_document_id: Optional[str] = None


class InsuranceResponse(BaseModel):
    """Insurance document extraction response"""
    document_type: str = "insurance"
    extracted: bool
    confidence: float
    fields: Dict[str, Any]
    source_document_id: Optional[str] = None


class ServiceBillResponse(BaseModel):
    """Service bill extraction response"""
    document_type: str = "service_bill"
    extracted: bool
    confidence: float
    fields: Dict[str, Any]
    source_document_id: Optional[str] = None


class DocumentExtractor:
    """
    OCR-based document extraction
    Uses Tesseract for text recognition and regex/pattern matching for field extraction
    """
    
    def __init__(self):
        self.base_confidence = 0.75  # Base confidence for extraction
        self.tesseract_available = self.check_tesseract_availability()
        self._rapid_ocr = None
        self._rapid_ocr_error = None
        self._rapid_ocr_lock = threading.Lock()
    
    def check_tesseract_availability(self):
        """Check if Tesseract is installed and accessible"""
        try:
            # Windows consoles may use cp1252 and cannot print the checkmark below.
            import sys
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(errors="replace")
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract OCR found: {version}")
        except pytesseract.TesseractNotFoundError:
            error_msg = (
                "✗ Tesseract OCR not found!\n"
                "Install with:\n"
                "  Windows: choco install tesseract\n"
                "  Mac: brew install tesseract\n"
                "  Linux: apt-get install tesseract-ocr"
            )
            print(error_msg)
            return False
        return True
    
    def preprocess_image(self, image, apply_preprocessing: bool = False):
        """
        Optional image preprocessing for better OCR results
        
        Args:
            image: PIL Image object
            apply_preprocessing: Whether to apply OpenCV preprocessing
        
        Returns:
            Preprocessed PIL Image (or original if OpenCV unavailable)
        """
        if not apply_preprocessing:
            return image
        
        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply adaptive thresholding for better text contrast
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            processed = cv2.fastNlMeansDenoising(processed, None, 10, 7, 21)
            
            # Convert back to PIL
            print("[PREPROCESS] Applied OpenCV preprocessing")
            return Image.fromarray(processed)
        
        except ImportError:
            print("[PREPROCESS] OpenCV not available, skipping preprocessing")
            return image
        except Exception as e:
            print(f"[PREPROCESS] Error during preprocessing: {e}, using original image")
            return image
    
    def extract_text_from_image(self, image_path: str, languages: str = 'eng+hin', preprocess: bool = False) -> tuple:
        """
        Extract text from image using Tesseract OCR with confidence scores
        
        Args:
            image_path: Path to image file
            languages: Language codes (e.g., 'eng', 'eng+hin' for English+Hindi)
            preprocess: Whether to apply OpenCV preprocessing for better OCR
        
        Returns:
            (text, average_confidence)
        """
        try:
            print(f"[OCR] Opening image: {image_path}")
            image = Image.open(image_path)
            print(f"[OCR] Image size: {image.size}, mode: {image.mode}")
            
            # Apply preprocessing if requested
            if preprocess:
                image = self.preprocess_image(image, apply_preprocessing=True)
            
            # Extract text with confidence data
            config = f'--psm 6 -l {languages}'
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            
            # Get confidence scores (filter out -1 which means word not found)
            confidences = [float(c) / 100.0 for c in data['conf'] if c != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Extract text
            text = pytesseract.image_to_string(image, config=config)
            
            print(f"[OCR] Extracted text length: {len(text)}")
            print(f"[OCR] Average OCR confidence: {avg_confidence:.2f}")
            print(f"[OCR] Languages: {languages}")
            print(f"[OCR] Text preview: {text[:200]}")
            
            return text, avg_confidence
        except Exception as e:
            print(f"[ERROR] Error extracting text: {e}")
            # If Hindi fails, fallback to English only
            if 'hin' in languages and languages != 'eng':
                print(f"[OCR] Retrying with English only...")
                return self.extract_text_from_image(image_path, languages='eng', preprocess=preprocess)
            return "", 0.0

    def _get_rapid_ocr(self):
        """Load the local pretrained OCR model once, on the first odometer request."""
        if self._rapid_ocr is not None:
            return self._rapid_ocr
        if self._rapid_ocr_error:
            return None
        with self._rapid_ocr_lock:
            if self._rapid_ocr is not None:
                return self._rapid_ocr
            try:
                from rapidocr import RapidOCR
                self._rapid_ocr = RapidOCR(params={"Global.use_cls": False})
            except Exception as exc:
                self._rapid_ocr_error = str(exc)
                print(f"[ODOMETER OCR] RapidOCR unavailable: {exc}")
        return self._rapid_ocr

    @staticmethod
    def _numeric_reading_candidate(raw_text: str, confidence: float, engine: str) -> Optional[Dict[str, Any]]:
        """Normalize one OCR line without allowing unrelated partial-number matches."""
        import re

        # Permit common odometer labels/units while rejecting VINs and other
        # mixed letter-number strings that happen to contain several digits.
        number_text = re.sub(
            r"\b(?:odometer|odo|mileage|reading|distance|range|trip|total|a)\b|(?:odometer|odo)(?=\d)|(?:kms?|miles?|mi)\b",
            "",
            raw_text,
            flags=re.IGNORECASE,
        )
        if re.search(r"[A-Za-z]", number_text):
            return None
        digits = re.sub(r"\D", "", number_text)
        if not 3 <= len(digits) <= 8:
            return None
        return {
            "value": digits,
            "confidence": round(max(0.0, min(float(confidence), 1.0)), 3),
            "engine": engine,
            "text": raw_text.strip(),
        }

    def extract_odometer_readings(self, image_path: str) -> Dict[str, Any]:
        """Recognize a complete odometer number with pretrained OCR and a Tesseract fallback."""
        import re
        import cv2
        import numpy as np
        from PIL import ImageOps

        image = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
        rgb = np.asarray(image)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        # Enlarge small dashboard photos before OCR; the odometer is often only
        # a small part of the full image. Keep already-large originals intact.
        scale = min(3.0, max(1.0, 2200.0 / max(image.size)))
        if scale > 1.0:
            bgr = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
        adaptive = cv2.adaptiveThreshold(
            clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 7
        )
        variants = [
            bgr,
            cv2.cvtColor(clahe, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(cv2.bitwise_not(adaptive), cv2.COLOR_GRAY2BGR),
        ]

        candidates = []
        raw_lines = []
        engine_names = []
        rapid_ocr = self._get_rapid_ocr()
        if rapid_ocr:
            for variant_index, variant in enumerate(variants):
                try:
                    result = rapid_ocr(variant, use_cls=False)
                    result_texts = getattr(result, "txts", None)
                    result_scores = getattr(result, "scores", None)
                    result_boxes = getattr(result, "boxes", None)
                    texts = list(result_texts) if result_texts is not None else []
                    scores = list(result_scores) if result_scores is not None else []
                    boxes = list(result_boxes) if result_boxes is not None else []
                    for index, text in enumerate(texts):
                        score = float(scores[index]) if index < len(scores) else 0.0
                        raw_lines.append(str(text))
                        candidate = self._numeric_reading_candidate(str(text), score, "RapidOCR")
                        if candidate:
                            candidate["variant"] = variant_index
                            candidates.append(candidate)

                    # Some displays are segmented into one box per digit. Rebuild
                    # numeric rows in left-to-right order from the detector boxes.
                    digit_boxes = []
                    for index, text in enumerate(texts):
                        digits = re.sub(r"\D", "", str(text))
                        if not digits or index >= len(boxes):
                            continue
                        points = np.asarray(boxes[index], dtype=float).reshape(-1, 2)
                        x0, x1 = float(points[:, 0].min()), float(points[:, 0].max())
                        y0, y1 = float(points[:, 1].min()), float(points[:, 1].max())
                        digit_boxes.append({
                            "digits": digits, "x0": x0, "x1": x1,
                            "cy": (y0 + y1) / 2, "height": max(1.0, y1 - y0),
                            "score": float(scores[index]) if index < len(scores) else 0.0,
                        })
                    rows = []
                    for item in sorted(digit_boxes, key=lambda box: (box["cy"], box["x0"])):
                        row = next((row for row in rows if abs(row["cy"] - item["cy"]) <= max(8.0, item["height"] * 0.55)), None)
                        if row is None:
                            rows.append({"cy": item["cy"], "items": [item]})
                        else:
                            row["items"].append(item)
                            row["cy"] = sum(part["cy"] for part in row["items"]) / len(row["items"])
                    for row in rows:
                        parts = sorted(row["items"], key=lambda box: box["x0"])
                        # Keep a whole-row reading candidate as well: some OCR
                        # detectors return each LCD digit (or digit pair) as a
                        # separate box with a gap too large for the tighter
                        # sequence splitter below.
                        row_value = "".join(item["digits"] for item in parts)
                        row_confidence = sum(item["score"] for item in parts) / len(parts)
                        candidate = self._numeric_reading_candidate(row_value, row_confidence, "RapidOCR-row")
                        if candidate:
                            candidate["variant"] = variant_index
                            candidates.append(candidate)

                        sequences = []
                        current = []
                        for item in parts:
                            if current and item["x0"] - current[-1]["x1"] > max(item["height"], current[-1]["height"]):
                                sequences.append(current)
                                current = []
                            current.append(item)
                        if current:
                            sequences.append(current)
                        for sequence in sequences:
                            value = "".join(item["digits"] for item in sequence)
                            confidence = sum(item["score"] for item in sequence) / len(sequence)
                            candidate = self._numeric_reading_candidate(value, confidence, "RapidOCR-segmented")
                            if candidate:
                                candidate["variant"] = variant_index
                                candidates.append(candidate)
                    if texts:
                        engine_names.append("RapidOCR")
                except Exception as exc:
                    print(f"[ODOMETER OCR] RapidOCR variant={variant_index} failed: {exc}")

        # Tesseract remains a second, independent recognizer. Use line-mode on
        # the enhanced and adaptive images instead of page-mode on the whole photo.
        if self.tesseract_available:
            tesseract_images = [Image.fromarray(cv2.cvtColor(variant, cv2.COLOR_BGR2RGB)) for variant in variants]
            for variant_index, variant in enumerate(tesseract_images):
                # PSM 6/11 handle displays where the odometer sits in a larger
                # dashboard photo; 7/13 handle tightly framed single-line digits.
                for psm in (6, 7, 11, 13):
                    config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789.,"
                    try:
                        data = pytesseract.image_to_data(variant, lang="eng", config=config, output_type=pytesseract.Output.DICT)
                        line = pytesseract.image_to_string(variant, lang="eng", config=config).strip()
                        if line:
                            raw_lines.append(line)
                        confs = [float(value) / 100 for value in data["conf"] if str(value) != "-1"]
                        candidate = self._numeric_reading_candidate(line, sum(confs) / len(confs) if confs else 0.0, "Tesseract")
                        if candidate:
                            candidate["variant"] = variant_index
                            candidate["psm"] = psm
                            candidates.append(candidate)
                    except Exception as exc:
                        print(f"[ODOMETER OCR] Tesseract variant={variant_index} psm={psm} failed: {exc}")
            if any(item["engine"] == "Tesseract" for item in candidates):
                engine_names.append("Tesseract")

        # Deduplicate by full reading and prefer the strongest independent score.
        best_by_value = {}
        for candidate in candidates:
            old = best_by_value.get(candidate["value"])
            if old is None or candidate["confidence"] > old["confidence"]:
                best_by_value[candidate["value"]] = candidate
        ranked = sorted(best_by_value.values(), key=lambda item: item["confidence"], reverse=True)
        confidence = ranked[0]["confidence"] if ranked else 0.0
        print(f"[ODOMETER OCR] engines={sorted(set(engine_names))}, candidates={ranked[:12]}")
        return {
            # Include reconstructed digit-box sequences in raw_text for older
            # backend processes that only consume the text field.
            "raw_text": "\n".join(dict.fromkeys(raw_lines + [item["value"] for item in ranked])),
            "reading_candidates": ranked[:20],
            "ocr_confidence": confidence,
            "ocr_engines": sorted(set(engine_names)),
            "ocr_error": self._rapid_ocr_error if not engine_names else None,
        }
    
    def extract_rc_info(self, text: str, ocr_confidence: float = 0.0) -> Dict[str, Any]:
        """
        Extract Registration Certificate fields from OCR text
        Uses multi-pattern matching for different state formats
        Returns per-field confidence scores (0.0-1.0)
        
        Args:
            text: OCR extracted text
            ocr_confidence: Average OCR confidence from Tesseract (0.0-1.0)
        """
        import re
        
        # Initialize with None and confidence tracking
        fields = {
            "registration_number": None,
            "owner": None,
            "model": None,
            "manufacturing_year": None,
            "registration_year": None,
            "fuel_type": None,
            "engine_displacement_cc": None,
            "power_bhp": None,
            "transmission": None,
            "vin": None
        }
        
        # Start with base OCR confidence, will be adjusted per field
        field_confidence = {key: 0.0 for key in fields.keys()}
        
        # ========== REGISTRATION NUMBER ==========
        # Try multiple state formats (TN, DL, KA, MH, etc.)
        reg_patterns = [
            r'(?:Reg\.?\s*No\.?|Registration|Reg)[:\s]*([A-Z]{2}\s*[-]?\d{2}\s*[-]?[A-Z]{2}\s*[-]?\d{4})',
            r'\b([A-Z]{2})\s*[-]?\s*(\d{2})\s*[-]?\s*([A-Z]{2})\s*[-]?\s*(\d{4})\b',
            r'\b([A-Z]{2}\d{2}[A-Z]{2}\d{4})\b',  # Compact format
        ]
        
        for pattern in reg_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract registration number, cleaning up spaces/hyphens
                if match.lastindex and match.lastindex >= 4:
                    reg_num = ''.join(match.groups()[:4])
                else:
                    reg_num = match.group(1) if match.lastindex else match.group(0)
                reg_num = re.sub(r'[\s-]+', '', reg_num).upper()
                if re.match(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$', reg_num):
                    fields["registration_number"] = f"{reg_num[:2]}-{reg_num[2:4]}-{reg_num[4:6]}-{reg_num[6:]}"
                    # Combine pattern confidence (0.95) with OCR confidence
                    field_confidence["registration_number"] = 0.95 * ocr_confidence
                    break
        
        # ========== VIN/CHASSIS NUMBER ==========
        # Try different VIN patterns
        vin_patterns = [
            r'(?:Chassis|VIN|Chassis\s*No\.?)[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'\b([A-HJ-NPR-Z0-9]{17})\b',
        ]
        
        for pattern in vin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vin = match.group(1) if match.lastindex else match.group(0)
                if len(vin) == 17:
                    fields["vin"] = vin
                    field_confidence["vin"] = 0.90 * ocr_confidence
                    break
        
        # ========== MANUFACTURING & REGISTRATION YEAR ==========
        # Look for year patterns (1900-2099)
        year_pattern = r'\b(1[89]\d{2}|20\d{2})\b'
        manufacturing_match = re.search(r'(?:manufacturing|manufacture|mfg)[^\n:]*[:\s]+(19\d{2}|20\d{2})', text, re.IGNORECASE)
        registration_match = re.search(r'(?:registration|registered)[^\n:]*[:\s]+(19\d{2}|20\d{2})', text, re.IGNORECASE)
        year_matches = re.findall(year_pattern, text)
        
        if year_matches:
            years = [int(y) for y in year_matches if 1900 <= int(y) <= 2050]
            years = list(dict.fromkeys(years))  # Remove duplicates, preserve order
            
            if manufacturing_match:
                fields["manufacturing_year"] = int(manufacturing_match.group(1))
                field_confidence["manufacturing_year"] = 0.85 * ocr_confidence
            elif len(years) >= 1:
                # First year is likely manufacturing year
                fields["manufacturing_year"] = years[0]
                field_confidence["manufacturing_year"] = 0.85 * ocr_confidence
            
            if registration_match:
                fields["registration_year"] = int(registration_match.group(1))
                field_confidence["registration_year"] = 0.80 * ocr_confidence
            elif len(years) >= 2:
                # Second year is likely registration year
                fields["registration_year"] = years[1]
                field_confidence["registration_year"] = 0.80 * ocr_confidence
        
        # ========== FUEL TYPE ==========
        fuel_keywords = {
            "petrol": [r'\bpetrol\b', r'\bbenzine\b', r'\bPETROL\b'],
            "diesel": [r'\bdiesel\b'],
            "cng": [r'\bCNG\b', r'\bcompressed\s+natural\s+gas\b'],
            "lpg": [r'\bLPG\b', r'\bliquified\s+petroleum\b'],
            "electric": [r'\belectric\b', r'\bEV\b'],
            "hybrid": [r'\bhybrid\b'],
        }
        
        for fuel_type, patterns in fuel_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    fields["fuel_type"] = fuel_type
                    field_confidence["fuel_type"] = 0.88 * ocr_confidence
                    break
            if fields["fuel_type"]:
                break
        
        # ========== ENGINE DISPLACEMENT ==========
        engine_patterns = [
            r'(?:Engine|Displacement|cc)[:\s]*(\d{3,4})\s*cc',
            r'(\d{3,4})\s*(?:cc|CC)',
        ]
        
        for pattern in engine_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cc = int(match.group(1))
                if 500 <= cc <= 7000:  # Reasonable range for cars
                    fields["engine_displacement_cc"] = cc
                    field_confidence["engine_displacement_cc"] = 0.92 * ocr_confidence
                    break
        
        # ========== POWER (BHP) ==========
        power_patterns = [
            r'(?:Power|BHP|bhp)[:\s]*(\d{1,3})\s*(?:bhp|BHP)',
            r'(\d{1,3})\s*(?:bhp|BHP)',
        ]
        
        for pattern in power_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bhp = int(match.group(1))
                if 40 <= bhp <= 400:  # Reasonable range
                    fields["power_bhp"] = bhp
                    field_confidence["power_bhp"] = 0.90 * ocr_confidence
                    break
        
        # ========== TRANSMISSION ==========
        if re.search(r'\bautomatic\b|\bauto\b', text, re.IGNORECASE):
            fields["transmission"] = "automatic"
            field_confidence["transmission"] = 0.85 * ocr_confidence
        elif re.search(r'\bmanual\b', text, re.IGNORECASE):
            fields["transmission"] = "manual"
            field_confidence["transmission"] = 0.85 * ocr_confidence
        
        # ========== VEHICLE MODEL ==========
        # Comprehensive list of Indian car models
        model_keywords = {
            'swift': 0.95,
            'alto': 0.95,
            'celerio': 0.95,
            'baleno': 0.95,
            'brezza': 0.90,
            'vitara': 0.90,
            'ertiga': 0.90,
            'ciaz': 0.90,
            'fortuner': 0.95,
            'innova': 0.95,
            'city': 0.95,
            'accord': 0.90,
            'civic': 0.90,
            'amaze': 0.90,
            'figo': 0.95,
            'aspire': 0.90,
            'polo': 0.95,
            'vento': 0.90,
            'jetta': 0.90,
            'skoda': 0.85,
            'tata': 0.80,
            'xuv': 0.85,
            'nexon': 0.90,
            'harrier': 0.90,
            'bolero': 0.90,
            'mahindra': 0.80,
            'scorpio': 0.90,
            'xylo': 0.85,
            'hyundai': 0.80,
            'i20': 0.90,
            'creta': 0.90,
            'verna': 0.90,
            'kia': 0.80,
            'seltos': 0.85,
            'renault': 0.80,
            'duster': 0.85,
            'kwid': 0.85,
            'nissan': 0.80,
            'datsun': 0.80,
            'mg': 0.80,
            'hector': 0.85,
            'bmw': 0.85,
            'audi': 0.85,
            'mercedes': 0.85,
            'toyota': 0.80,
            'etios': 0.85,
            'maruti': 0.75,
            'pulsar': 0.85,
            'bajaj': 0.80,
        }
        
        for keyword, confidence in sorted(model_keywords.items(), key=lambda x: -x[1]):
            if keyword.lower() in text.lower():
                fields["model"] = keyword.title()
                # Multiply keyword confidence with OCR confidence
                field_confidence["model"] = confidence * ocr_confidence
                break
        
        # ========== OWNER NAME ==========
        # Try multiple owner patterns (different document formats)
        owner_patterns = [
            r'(?:Owner\s+Name|Owner|Registered\s+to|Proprietor)\s*[:\-]\s*([A-Z][A-Za-z\s\.,]+?)(?:\n|$)',
            r'(?:Name)\s*[:\-]\s*([A-Z][A-Za-z\s\.,]+?)(?:\n|$)',
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                owner = match.group(1).strip()
                # Filter out common non-name strings
                if len(owner) > 2 and not re.search(r'(?:Government|Authority|Department)', owner, re.IGNORECASE):
                    fields["owner"] = owner
                    field_confidence["owner"] = 0.80 * ocr_confidence
                    break
        
        return {
            **fields,
            "extracted_fields": fields,
            "field_confidence": field_confidence,
            "overall_confidence": sum(field_confidence.values()) / len(field_confidence) if field_confidence else 0.0
        }
    
    def extract_insurance_info(self, text: str) -> Dict[str, Any]:
        """Extract Insurance policy fields from OCR text"""
        import re
        
        fields = {
            "policy_number": None,
            "valid_from": None,
            "valid_until": None,
            "insurer_name": None,
            "claims": []
        }
        
        # Policy number (alphanumeric, usually 10-20 chars)
        policy_pattern = r'policy\s*(?:number|no\.?)[:\s]+([A-Z0-9\-]{8,20})'
        policy_match = re.search(policy_pattern, text, re.IGNORECASE)
        if policy_match:
            fields["policy_number"] = policy_match.group(1).strip()
        
        # Valid dates (DD-MM-YYYY or YYYY-MM-DD)
        date_pattern = r'(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})'
        date_matches = re.findall(date_pattern, text)
        if len(date_matches) >= 1:
            fields["valid_from"] = date_matches[0]
        if len(date_matches) >= 2:
            fields["valid_until"] = date_matches[1]
        
        # Insurer names
        insurers = ['bajaj', 'hdfc', 'icici', 'tata', 'reliance', 'iffco', 
                   'national', 'united', 'oriental', 'edelweiss']
        for insurer in insurers:
            if insurer.lower() in text.lower():
                fields["insurer_name"] = insurer.title()
                break
        
        # Claims (look for claim amount patterns)
        claim_pattern = r'claim[:\s]+₹?(\d+(?:,\d+)*)'
        claim_matches = re.findall(claim_pattern, text, re.IGNORECASE)
        if claim_matches:
            for amount_str in claim_matches:
                amount = int(amount_str.replace(',', ''))
                fields["claims"].append({
                    "claim_id": f"CLM-{str(uuid.uuid4())[:8].upper()}",
                    "amount": amount,
                    "description": "Claim amount found in document"
                })
        
        return fields
    
    def extract_service_history(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract service bill information from OCR text
        Supports multiple service records in a single document
        """
        import re
        
        service_records = []
        
        # Split text into sections by looking for date patterns
        # Dates usually indicate separate service entries
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        
        # Find all dates and their positions
        date_matches = list(re.finditer(date_pattern, text))
        
        if not date_matches:
            # No dates found, treat as single record
            sections = [text]
        else:
            # Split text by date positions
            sections = []
            for i, match in enumerate(date_matches):
                start = match.start()
                # Go back 100 chars to capture context before date
                section_start = max(0, start - 100)
                
                # Section ends at next date or end of text
                if i + 1 < len(date_matches):
                    section_end = date_matches[i + 1].start()
                else:
                    section_end = len(text)
                
                sections.append(text[section_start:section_end])
        
        # Extract service record from each section
        for section in sections:
            record = self._extract_single_service_record(section)
            if record:  # Only add if we extracted something useful
                service_records.append(record)
        
        return service_records
    
    def _extract_single_service_record(self, text: str) -> Dict[str, Any]:
        """Extract a single service record from text section"""
        import re
        
        # Service date pattern
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        date_match = re.search(date_pattern, text)
        
        # Mileage pattern (e.g., 45000 km, 12,000 km)
        mileage_pattern = r'(?:mileage|odometer|km)[:\s]*(\d+(?:,\d+)*)\s*km'
        mileage_match = re.search(mileage_pattern, text, re.IGNORECASE)
        if not mileage_match:
            # Try standalone km pattern
            mileage_match = re.search(r'(\d{4,6})\s*km', text, re.IGNORECASE)
        
        # Service center (look for common patterns)
        service_center_patterns = [
            r'service\s*(?:center|centre)[:\s]+([^\n]{1,50})',
            r'(?:at|@)\s+([A-Z][A-Za-z\s&]{3,30}(?:Service|Motors|Auto|Garage))',
        ]
        service_center = None
        for pattern in service_center_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                service_center = match.group(1).strip()
                break
        
        # Cost pattern (e.g., ₹2500 or Rs. 2500 or Total Cost: 1400)
        cost_patterns = [
            r'(?:total|amount|cost)[:\s]*₹?\s*(\d+(?:,\d+)*)',
            r'₹\s*(\d+(?:,\d+)*)',
            r'rs\.?\s*(\d+(?:,\d+)*)',
        ]
        final_cost = None
        all_costs = []
        for pattern in cost_patterns:
            cost_matches = re.findall(pattern, text, re.IGNORECASE)
            all_costs.extend([int(m.replace(',', '')) for m in cost_matches])
        
        # Take the highest cost value (usually the total)
        if all_costs:
            final_cost = max(all_costs)
        
        # Work done keywords
        work_keywords = [
            'oil change', 'engine oil', 'filter replacement', 'air filter',
            'oil filter', 'fuel filter', 'battery', 'battery replacement',
            'spark plug', 'coolant', 'coolant top up', 'brake fluid',
            'tire rotation', 'wheel alignment', 'wheel balancing',
            'general service', 'periodic maintenance', 'inspection',
            'brake pad', 'wiper blade', 'ac service', 'ac gas',
            'transmission fluid', 'power steering', 'suspension',
        ]
        
        work_done = []
        for keyword in work_keywords:
            if keyword.lower() in text.lower() and keyword.title() not in work_done:
                work_done.append(keyword.title())
        
        # Parts replaced - look for specific part mentions
        parts_replaced = []
        part_keywords = [
            'filter', 'battery', 'spark plug', 'brake pad',
            'wiper', 'belt', 'gasket', 'sensor'
        ]
        for part in part_keywords:
            if part.lower() in text.lower():
                parts_replaced.append(part.title())
        
        # Only create record if we have at least one useful field
        if date_match or mileage_match or service_center or final_cost or work_done:
            return {
                "service_id": f"SRV-{str(uuid.uuid4())[:8].upper()}",
                "date": date_match.group(1) if date_match else None,
                "mileage_km": int(mileage_match.group(1).replace(',', '')) if mileage_match else None,
                "service_center": service_center,
                "work_done": work_done if work_done else ["General Service"],
                "parts_replaced": parts_replaced,
                "cost": final_cost,
                "currency": "INR" if final_cost else None
            }
        
        return None


# Initialize extractor
extractor = DocumentExtractor()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Document AI",
        "version": "0.1.0",
        "ocr_available": extractor.tesseract_available,
        "odometer_ocr_available": importlib.util.find_spec("rapidocr") is not None,
    }


@app.post("/extract", response_model=Dict[str, Any])
async def extract_document(file: UploadFile = File(...), document_type: str = "rc", ocr_mode: str = "document"):
    """
    Extract information from uploaded document
    
    Args:
        file: PDF or image file
        document_type: "rc", "insurance", or "service_bill"
    
    Returns:
        Extracted fields with confidence scores
    """
    try:
        # VALIDATION: Check file format
        allowed_extensions = ["pdf", "jpg", "jpeg", "png", "bmp", "tiff", "webp"]
        file_ext = file.filename.split(".")[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # VALIDATION: Check file size (read content first)
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(content) > 20 * 1024 * 1024:  # 20MB
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size: 20MB"
            )
        
        # VALIDATION: For images, verify they're valid
        if file_ext in ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]:
            try:
                test_image = Image.open(io.BytesIO(content))
                test_image.verify()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid or corrupted image file: {str(e)}"
                )
        
        # VALIDATION: For PDFs, check magic bytes
        if file_ext == "pdf":
            if content[:4] != b'%PDF':
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file (magic bytes check failed)"
                )
        
        # Save uploaded file
        import tempfile
        doc_id = f"DOC-{str(uuid.uuid4())[:8].upper()}"
        
        # Handle different file types
        odometer_ocr = None
        if file.filename.lower().endswith('.pdf'):
            # Extract embedded text first; OCR scanned pages after rendering.
            try:
                extracted_text = ""
                total_confidence = 0.0
                page_count = 0
                try:
                    import fitz
                    pdf = fitz.open(stream=content, filetype="pdf")
                    page_count = len(pdf)
                    for page in pdf:
                        page_text = page.get_text("text").strip()
                        if page_text:
                            extracted_text += page_text + "\n"
                            continue
                        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_page:
                            image.save(tmp_page.name)
                            page_path = tmp_page.name
                        try:
                            page_text, page_confidence = extractor.extract_text_from_image(page_path)
                            extracted_text += page_text + "\n"
                            total_confidence += page_confidence
                        finally:
                            os.remove(page_path)
                    pdf.close()
                except ImportError:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(content, dpi=250)
                    page_count = len(images)
                    for image in images:
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_page:
                            image.save(tmp_page.name)
                            page_path = tmp_page.name
                        try:
                            page_text, page_confidence = extractor.extract_text_from_image(page_path)
                            extracted_text += page_text + "\n"
                            total_confidence += page_confidence
                        finally:
                            os.remove(page_path)
                ocr_confidence = total_confidence / page_count if page_count and total_confidence else (1.0 if extracted_text.strip() else 0.0)
                print(f"[PDF] Extracted {len(extracted_text)} chars from {page_count} pages, OCR confidence: {ocr_confidence:.2f}")
            except Exception as e:
                print(f"[ERROR] PDF extraction failed: {e}")
                raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")
        else:
            # Save image file to temp directory
            image = Image.open(io.BytesIO(content))
            if ocr_mode == "odometer":
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
            
            # Use system temp directory (Windows/Linux compatible)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                temp_path = tmp_file.name
                image.save(temp_path)
            
            try:
                if ocr_mode == "odometer":
                    odometer_ocr = extractor.extract_odometer_readings(temp_path)
                    extracted_text = odometer_ocr["raw_text"]
                    ocr_confidence = odometer_ocr["ocr_confidence"]
                else:
                    odometer_ocr = None
                    extracted_text, ocr_confidence = extractor.extract_text_from_image(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        # Extract based on document type
        if document_type.lower() == "rc":
            print(f"\n[EXTRACT RC] File: {file.filename}")
            print(f"[EXTRACT RC] Extracted text length: {len(extracted_text)}")
            print(f"[EXTRACT RC] Text preview: {extracted_text[:300]}\n")
            
            # Pass OCR confidence to extract_rc_info
            extraction_result = extractor.extract_rc_info(extracted_text, ocr_confidence)
            fields = extraction_result["extracted_fields"]
            field_confidence = extraction_result["field_confidence"]
            overall_confidence = extraction_result["overall_confidence"]
            
            print(f"[EXTRACT RC] Fields: {fields}")
            print(f"[EXTRACT RC] Overall confidence: {overall_confidence}\n")
            
            response = {
                "document_type": "rc",
                "extracted": any(v is not None for v in fields.values()),
                "confidence": overall_confidence,
                "ocr_confidence": ocr_confidence,  # Include OCR confidence separately
                "fields": fields,
                "field_confidence": field_confidence,  # Per-field confidence scores
                "source_document_id": doc_id
            }
        
        elif document_type.lower() == "insurance":
            fields = extractor.extract_insurance_info(extracted_text)
            confidence = 0.88
            response = {
                "document_type": "insurance",
                "extracted": True,
                "confidence": confidence,
                "fields": fields,
                "raw_text": extracted_text,  # Always include raw text for debugging
                "source_document_id": doc_id
            }
        
        elif document_type.lower() == "service_bill":
            fields = extractor.extract_service_history(extracted_text)
            confidence = 0.85
            response = {
                "document_type": "service_bill",
                "extracted": True,
                "confidence": confidence,
                "fields": {
                    "service_records": fields,
                    "raw_text": extracted_text[:500]  # First 500 chars for verification
                },
                "source_document_id": doc_id
            }

        elif document_type.lower() == "text":
            response = {
                "document_type": "text",
                "extracted": bool(extracted_text.strip()),
                "confidence": ocr_confidence,
                "ocr_confidence": ocr_confidence,
                "raw_text": extracted_text,
                "source_document_id": doc_id,
            }
            if ocr_mode == "odometer":
                response["reading_candidates"] = odometer_ocr["reading_candidates"] if odometer_ocr else []
                response["ocr_engines"] = odometer_ocr["ocr_engines"] if odometer_ocr else []
                response["ocr_error"] = odometer_ocr["ocr_error"] if odometer_ocr else "No OCR result"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown document type: {document_type}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Exception in extract_document:")
        print(f"[ERROR] Type: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/extract/rc")
async def extract_rc(file: UploadFile = File(...)):
    """Extract RC (Registration Certificate) document"""
    return await extract_document(file, "rc")


@app.post("/extract/insurance")
async def extract_insurance(file: UploadFile = File(...)):
    """Extract Insurance document"""
    return await extract_document(file, "insurance")


@app.post("/extract/service")
async def extract_service_bill(file: UploadFile = File(...)):
    """Extract Service Bill document"""
    return await extract_document(file, "service_bill")


@app.post("/extract/text")
async def extract_document_text(file: UploadFile = File(...), mode: str = Form("document")):
    """OCR a PDF or image and return recognized text for field matching."""
    # Older backend processes do not send a mode field. Preserve compatibility
    # with already-running app code for odometer uploads named by the UI.
    if mode == "document" and "odometer" in (file.filename or "").lower():
        mode = "odometer"
    if mode not in {"document", "odometer"}:
        raise HTTPException(status_code=400, detail="mode must be 'document' or 'odometer'")
    return await extract_document(file, "text", ocr_mode=mode)


@app.post("/extract/odometer")
async def extract_odometer(file: UploadFile = File(...)):
    """Read numeric odometer displays through the dedicated odometer OCR pipeline."""
    allowed_image_extensions = {"jpg", "jpeg", "png", "bmp", "tiff", "webp"}
    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    if extension not in allowed_image_extensions:
        raise HTTPException(status_code=400, detail="Odometer upload must be a JPG, PNG, BMP, TIFF, or WEBP image")
    return await extract_document(file, "text", ocr_mode="odometer")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "CarVal Document AI",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "extract": "/extract",
            "extract_rc": "/extract/rc",
            "extract_insurance": "/extract/insurance",
            "extract_service": "/extract/service"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )

