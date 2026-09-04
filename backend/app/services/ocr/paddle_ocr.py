import os
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ocr_result import OCRResult

logger = logging.getLogger(__name__)

# Ensure model source check does not block in offline/restricted environments
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"


def _apply_windows_paddle_cpu_patch():
    """
    Applies compatibility patch for PaddlePaddle 3.x / PaddleX on Windows CPU.
    Resolves PIR (New IR) / oneDNN attribute mismatch:
    (ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]).
    Forces stable legacy IR and native CPU execution mode.
    """
    try:
        from paddlex.inference.models.runners.paddle_static import runner
        if not getattr(runner, "_sih_cpu_patched", False):
            orig_create = runner.PaddleStaticRunner._create

            def safe_cpu_create(self):
                # Set legacy IR and native paddle execution for CPU
                if self._config.get("device_type", "cpu") == "cpu":
                    self._config["enable_new_ir"] = False
                    self._config["run_mode"] = "paddle"
                return orig_create(self)

            runner.PaddleStaticRunner._create = safe_cpu_create
            runner._sih_cpu_patched = True
            logger.info("PaddleX Windows CPU compatibility patch applied successfully.")
    except Exception as e:
        logger.warning(f"Could not apply PaddleX Windows CPU patch: {e}")


class PaddleOCRService:
    """
    Singleton service wrapper around PaddleOCR for fast, deterministic text
    and bounding box extraction from packaging label images.
    """
    _instance: Optional["PaddleOCRService"] = None
    _ocr_engine = None

    def __init__(self):
        _apply_windows_paddle_cpu_patch()
        self._init_engine()

    @classmethod
    def get_instance(cls) -> "PaddleOCRService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_engine(self):
        if self._ocr_engine is None:
            try:
                from paddleocr import PaddleOCR
                # Initialize English OCR pipeline
                self._ocr_engine = PaddleOCR(lang="en")
                logger.info("PaddleOCR engine initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing PaddleOCR engine: {e}")
                raise

    def process_image(self, image_path: str, image_id: str) -> List[Dict[str, Any]]:
        """
        Run OCR detection and recognition on an image file.
        Returns extracted text lines, confidence scores, and bounding boxes.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        extracted_lines = []

        try:
            # Predict using PaddleX/PaddleOCR pipeline
            results = self._ocr_engine.predict(image_path)

            for res in results:
                # Handle PaddleOCR 3.x result dictionary structure
                if isinstance(res, dict) or hasattr(res, "__getitem__"):
                    rec_texts = res.get("rec_texts", [])
                    rec_scores = res.get("rec_scores", [])
                    rec_boxes = res.get("rec_boxes", [])
                    rec_polys = res.get("rec_polys", [])

                    for idx, text in enumerate(rec_texts):
                        clean_text = str(text).strip()
                        if not clean_text:
                            continue

                        score = float(rec_scores[idx]) if idx < len(rec_scores) else 0.9

                        # Extract bounding box [x_min, y_min, x_max, y_max]
                        bbox = [0, 0, 0, 0]
                        if idx < len(rec_boxes):
                            raw_box = rec_boxes[idx]
                            bbox = [int(val) for val in raw_box]

                        # Extract 4-point polygon [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        poly_points = None
                        if idx < len(rec_polys):
                            raw_poly = rec_polys[idx]
                            poly_points = [[int(pt[0]), int(pt[1])] for pt in raw_poly]

                        extracted_lines.append({
                            "image_id": image_id,
                            "text": clean_text,
                            "confidence": round(score, 4),
                            "bbox": bbox,
                            "polygon": poly_points,
                            "line_order": idx
                        })

                # Fallback for classic PaddleOCR 2.x list-of-lists format
                elif isinstance(res, list):
                    for idx, line in enumerate(res):
                        if not line or len(line) < 2:
                            continue
                        points = line[0]
                        text_info = line[1]
                        text = str(text_info[0]).strip()
                        conf = float(text_info[1])

                        min_x = int(min(p[0] for p in points))
                        min_y = int(min(p[1] for p in points))
                        max_x = int(max(p[0] for p in points))
                        max_y = int(max(p[1] for p in points))

                        extracted_lines.append({
                            "image_id": image_id,
                            "text": text,
                            "confidence": round(conf, 4),
                            "bbox": [min_x, min_y, max_x, max_y],
                            "polygon": [[int(p[0]), int(p[1])] for p in points],
                            "line_order": idx
                        })

        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {e}")
            raise

        return extracted_lines

    @staticmethod
    def save_ocr_results_to_db(
        db: Session,
        scan_id: str,
        image_id: str,
        extracted_lines: List[Dict[str, Any]]
    ) -> List[OCRResult]:
        """Persist detected OCR text lines and bounding boxes into the database."""
        db_records = []
        for item in extracted_lines:
            record = OCRResult(
                scan_id=scan_id,
                image_id=image_id,
                text=item["text"],
                confidence=item["confidence"],
                bbox_json=json.dumps({
                    "bbox": item["bbox"],
                    "polygon": item.get("polygon")
                }),
                line_order=item["line_order"]
            )
            db.add(record)
            db_records.append(record)

        db.commit()
        for r in db_records:
            db.refresh(r)
        return db_records
