import os
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ocr_result import OCRResult

logger = logging.getLogger(__name__)

# Ensure model source check does not block in offline/restricted environments
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"


def _is_numeric_point(pt: Any) -> bool:
    if not isinstance(pt, (list, tuple)) or len(pt) < 2:
        return False
    try:
        float(pt[0])
        float(pt[1])
        return True
    except (TypeError, ValueError):
        return False


def _is_classic_ocr_line(item: Any) -> bool:
    """PaddleOCR 2.x line: [points, (text, confidence)]."""
    if not isinstance(item, (list, tuple)) or len(item) < 2:
        return False
    points, text_info = item[0], item[1]
    if not isinstance(points, (list, tuple)) or len(points) < 2:
        return False
    if not _is_numeric_point(points[0]):
        return False
    return isinstance(text_info, (list, tuple, str))


def _mapping_get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, key):
        val = getattr(obj, key)
        if val is not None:
            return val
    getter = getattr(obj, "get", None)
    if callable(getter) and not isinstance(obj, (list, tuple)):
        try:
            return getter(key, default)
        except TypeError:
            pass
    return default


def _has_rec_texts(obj: Any) -> bool:
    texts = _mapping_get(obj, "rec_texts")
    return texts is not None and not isinstance(obj, (list, tuple))


def _as_sequence(values: Any) -> List[Any]:
    """Turn lists / tuples / numpy arrays into a plain list without using truthiness."""
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        return [values]
    if hasattr(values, "tolist") and not isinstance(values, (list, tuple)):
        try:
            values = values.tolist()
        except Exception:
            pass
    if isinstance(values, (list, tuple)):
        return list(values)
    try:
        return list(values)
    except TypeError:
        return []


def _as_int_list(values: Any) -> List[int]:
    seq = _as_sequence(values)
    try:
        return [int(v) for v in seq]
    except (TypeError, ValueError):
        return [0, 0, 0, 0]


def _parse_classic_page(page: Any, image_id: str, order_start: int) -> List[Dict[str, Any]]:
    extracted = []
    if not isinstance(page, (list, tuple)):
        return extracted
    for idx, line in enumerate(page):
        if not _is_classic_ocr_line(line):
            continue
        points = line[0]
        text_info = line[1]
        if isinstance(text_info, str):
            text = text_info.strip()
            conf = 0.9
        else:
            text = str(text_info[0]).strip()
            conf = float(text_info[1]) if len(text_info) > 1 else 0.9
        if not text:
            continue
        min_x = int(min(p[0] for p in points))
        min_y = int(min(p[1] for p in points))
        max_x = int(max(p[0] for p in points))
        max_y = int(max(p[1] for p in points))
        extracted.append({
            "image_id": image_id,
            "text": text,
            "confidence": round(conf, 4),
            "bbox": [min_x, min_y, max_x, max_y],
            "polygon": [[int(p[0]), int(p[1])] for p in points],
            "line_order": order_start + idx,
        })
    return extracted


def _parse_rec_mapping(res: Any, image_id: str, order_start: int) -> List[Dict[str, Any]]:
    rec_texts = _as_sequence(_mapping_get(res, "rec_texts", None))
    rec_scores = _as_sequence(_mapping_get(res, "rec_scores", None))
    rec_boxes = _as_sequence(_mapping_get(res, "rec_boxes", None))
    rec_polys = _as_sequence(_mapping_get(res, "rec_polys", None))
    extracted = []
    for idx, text in enumerate(rec_texts):
        clean_text = str(text).strip()
        if not clean_text:
            continue
        score = float(rec_scores[idx]) if idx < len(rec_scores) else 0.9
        bbox = [0, 0, 0, 0]
        if idx < len(rec_boxes):
            bbox = _as_int_list(rec_boxes[idx])
        poly_points = None
        if idx < len(rec_polys):
            raw_poly = rec_polys[idx]
            try:
                poly_points = [[int(pt[0]), int(pt[1])] for pt in raw_poly]
            except (TypeError, ValueError, IndexError):
                poly_points = None
        extracted.append({
            "image_id": image_id,
            "text": clean_text,
            "confidence": round(score, 4),
            "bbox": bbox,
            "polygon": poly_points,
            "line_order": order_start + idx,
        })
    return extracted


def parse_paddle_ocr_results(results: Any, image_id: str) -> List[Dict[str, Any]]:
    """
    Normalize PaddleOCR 2.x list-of-lines and 3.x rec_texts mappings into
    the same line dictionaries. Lists must be handled before dict-like access
    because lists implement __getitem__ but not .get.
    """
    if results is None:
        return []

    pages: List[Any]
    if _has_rec_texts(results) or isinstance(results, dict):
        pages = [results]
    elif isinstance(results, (list, tuple)):
        if results and _is_classic_ocr_line(results[0]):
            pages = [results]
        else:
            pages = list(results)
    else:
        pages = [results]

    extracted_lines: List[Dict[str, Any]] = []
    for res in pages:
        parsed = _parse_rec_mapping(res, image_id, len(extracted_lines)) if _has_rec_texts(res) or isinstance(res, dict) else []
        if not parsed and isinstance(res, (list, tuple)):
            if res and _is_classic_ocr_line(res[0]):
                parsed = _parse_classic_page(res, image_id, len(extracted_lines))
            elif res and isinstance(res[0], (list, tuple)) and res[0] and _is_classic_ocr_line(res[0][0]):
                parsed = _parse_classic_page(res[0], image_id, len(extracted_lines))
        extracted_lines.extend(parsed)
    return extracted_lines


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
                self._ocr_engine = None

    @property
    def available(self) -> bool:
        return self._ocr_engine is not None

    def process_image(self, image_path: str, image_id: str) -> List[Dict[str, Any]]:
        """
        Run OCR detection and recognition on an image file.
        Returns extracted text lines, confidence scores, and bounding boxes.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        if self._ocr_engine is None:
            logger.warning("PaddleOCR is not installed; skipping OCR for %s", image_path)
            return []

        try:
            if hasattr(self._ocr_engine, "predict"):
                results = self._ocr_engine.predict(image_path)
            else:
                results = self._ocr_engine.ocr(image_path)
            lines = parse_paddle_ocr_results(results, image_id)
            logger.info("OCR extracted %s line(s) from %s", len(lines), image_path)
            return lines
        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {e}")
            raise

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
