import os
import cv2
import numpy as np
from typing import Optional, Dict, Any, Union
from app.services.vision.preprocessing import ImagePreprocessor


class BarcodeService:
    """
    Automated 1D/2D Barcode Detection Service using OpenCV.
    Detects standard retail barcodes (EAN-13, EAN-8, UPC-A, Code 128, Code 39)
    and QR codes from packaged commodity label photographs.
    """

    _barcode_detector: Optional[cv2.barcode.BarcodeDetector] = None
    _qr_detector: Optional[cv2.QRCodeDetector] = None

    @classmethod
    def _get_barcode_detector(cls) -> cv2.barcode.BarcodeDetector:
        if cls._barcode_detector is None:
            cls._barcode_detector = cv2.barcode.BarcodeDetector()
        return cls._barcode_detector

    @classmethod
    def _get_qr_detector(cls) -> cv2.QRCodeDetector:
        if cls._qr_detector is None:
            cls._qr_detector = cv2.QRCodeDetector()
        return cls._qr_detector

    @classmethod
    def detect_barcode(cls, image_input: Union[str, np.ndarray]) -> Dict[str, Any]:
        """
        Detect and decode barcode or QR code from image file path or numpy array.
        Includes multi-rotation fallback to handle labels photographed at various angles.
        """
        if isinstance(image_input, str):
            img = ImagePreprocessor.read_image_safe(image_input)
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            img = None

        if img is None:
            return {
                "found": False,
                "barcode": None,
                "type": None,
                "confidence": 0.0,
                "method": None
            }

        # Try orientations: original, 90 deg clockwise, 180 deg, 270 deg
        orientations = [
            ("0", img),
            ("90", cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)),
            ("180", cv2.rotate(img, cv2.ROTATE_180)),
            ("270", cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)),
        ]

        barcode_detector = cls._get_barcode_detector()
        qr_detector = cls._get_qr_detector()

        for angle_name, candidate_img in orientations:
            # 1. Check 1D Barcode: returns (decoded_info, points, decoded_type)
            try:
                ret = barcode_detector.detectAndDecode(candidate_img)
                if ret and len(ret) >= 1 and isinstance(ret[0], str) and ret[0].strip():
                    clean_code = ret[0].strip()
                    b_type = "EAN_UPC" if len(clean_code) in (8, 12, 13, 14) and clean_code.isdigit() else "BARCODE_1D"
                    return {
                        "found": True,
                        "barcode": clean_code,
                        "type": b_type,
                        "confidence": 0.95,
                        "method": "opencv_barcode_detector",
                        "orientation": angle_name
                    }
            except Exception:
                pass

            # 2. Check 2D QR Code: returns (decoded_info, points, straight_qrcode)
            try:
                ret_qr = qr_detector.detectAndDecode(candidate_img)
                if ret_qr and len(ret_qr) >= 1 and isinstance(ret_qr[0], str) and ret_qr[0].strip():
                    clean_qr = ret_qr[0].strip()
                    return {
                        "found": True,
                        "barcode": clean_qr,
                        "type": "QR_CODE",
                        "confidence": 0.95,
                        "method": "opencv_qr_detector",
                        "orientation": angle_name
                    }
            except Exception:
                pass

        # If not detected directly, try contrast-enhanced grayscale version
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

            ret_enh = barcode_detector.detectAndDecode(enhanced_bgr)
            if ret_enh and len(ret_enh) >= 1 and isinstance(ret_enh[0], str) and ret_enh[0].strip():
                clean_code = ret_enh[0].strip()
                b_type = "EAN_UPC" if len(clean_code) in (8, 12, 13, 14) and clean_code.isdigit() else "BARCODE_1D"
                return {
                    "found": True,
                    "barcode": clean_code,
                    "type": b_type,
                    "confidence": 0.90,
                    "method": "opencv_enhanced_detector",
                    "orientation": "0_enhanced"
                }
        except Exception:
            pass

        return {
            "found": False,
            "barcode": None,
            "type": None,
            "confidence": 0.0,
            "method": None
        }
